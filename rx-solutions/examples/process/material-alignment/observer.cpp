// Package-owned FILE_SIMULATION observation process. No Host/P authority or cache.
// Execute and lookup replace this process with the pinned Python adapter unchanged.
#include <nlohmann/json.hpp>
#include <openssl/evp.h>

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <fcntl.h>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/file.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#include <utility>
#include <vector>

using Json = nlohmann::json;
constexpr std::size_t kMaximumBytes = 1'048'576;

namespace {
void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}

class Descriptor {
 public:
  explicit Descriptor(int value) : value_(value) {
    require(value >= 0, "cannot open owned regular file/directory");
  }
  ~Descriptor() { if (value_ >= 0) ::close(value_); }
  Descriptor(const Descriptor&) = delete;
  Descriptor& operator=(const Descriptor&) = delete;
  Descriptor(Descriptor&& other) noexcept : value_(std::exchange(other.value_, -1)) {}
  Descriptor& operator=(Descriptor&& other) noexcept {
    if (this != &other) {
      if (value_ >= 0) ::close(value_);
      value_ = std::exchange(other.value_, -1);
    }
    return *this;
  }
  int get() const { return value_; }
 private:
  int value_;
};

// Walk every path component with O_NOFOLLOW; an ancestor alias cannot bypass the
// regular-file/directory boundary. Ancestors may be root-owned installation paths.
Descriptor open_path(const std::string& path, int flags) {
  require(!path.empty() && path.front() == '/', "absolute installed path required");
  Descriptor current(::open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC));
  std::vector<std::string> components;
  std::istringstream stream(path);
  std::string component;
  while (std::getline(stream, component, '/')) {
    if (component.empty()) continue;
    require(component != "." && component != "..", "path traversal/alias refused");
    components.push_back(component);
  }
  require(!components.empty(), "installed leaf path required");
  for (std::size_t index = 0; index < components.size(); ++index) {
    const int requested = index + 1 == components.size() ? flags : O_RDONLY | O_DIRECTORY;
    current = Descriptor(::openat(current.get(), components[index].c_str(),
                                  requested | O_NOFOLLOW | O_CLOEXEC));
  }
  return current;
}

struct stat metadata(int descriptor) {
  struct stat value {};
  require(::fstat(descriptor, &value) == 0, "cannot inspect owned file/directory");
  return value;
}

void owned_regular(int descriptor) {
  const auto info = metadata(descriptor);
  require(S_ISREG(info.st_mode) && info.st_uid == ::getuid() && info.st_size >= 0 &&
              static_cast<std::uint64_t>(info.st_size) <= kMaximumBytes,
          "bounded owned regular file required");
}

Descriptor owned_directory(const std::string& path) {
  auto descriptor = open_path(path, O_RDONLY | O_DIRECTORY);
  const auto info = metadata(descriptor.get());
  require(S_ISDIR(info.st_mode) && info.st_uid == ::getuid(), "owned directory required");
  return descriptor;
}

std::string bounded_read(int descriptor) {
  std::string result;
  char buffer[8192];
  while (true) {
    const auto size = ::read(descriptor, buffer, sizeof(buffer));
    if (size < 0 && errno == EINTR) continue;
    require(size >= 0, "bounded read failed");
    if (size == 0) return result;
    require(result.size() + static_cast<std::size_t>(size) <= kMaximumBytes,
            "native request/file exceeds bound");
    result.append(buffer, static_cast<std::size_t>(size));
  }
}

std::string read_owned(const std::string& path) {
  auto descriptor = open_path(path, O_RDONLY);
  owned_regular(descriptor.get());
  return bounded_read(descriptor.get());
}

std::string read_owned_at(int root, const char* name) {
  Descriptor descriptor(::openat(root, name, O_RDONLY | O_NOFOLLOW | O_CLOEXEC));
  owned_regular(descriptor.get());
  return bounded_read(descriptor.get());
}

Json parse(const std::string& raw) {
  std::vector<std::set<std::string>> object_keys;
  return Json::parse(raw, [&](int depth, Json::parse_event_t event, Json& value) {
    require(depth <= 64, "JSON nesting exceeds bound");
    if (event == Json::parse_event_t::object_start) object_keys.emplace_back();
    if (event == Json::parse_event_t::key) {
      require(!object_keys.empty() && object_keys.back().insert(value.get<std::string>()).second,
              "duplicate JSON key refused");
    }
    if (event == Json::parse_event_t::object_end) object_keys.pop_back();
    return true;
  });
}

void keys(const Json& value, const std::set<std::string>& expected) {
  require(value.is_object(), "JSON object required");
  std::set<std::string> actual;
  for (const auto& entry : value.items()) actual.insert(entry.key());
  require(actual == expected, "closed JSON shape differs");
}

std::string text(const Json& value) {
  require(value.is_string(), "text value required");
  return value.get<std::string>();
}

bool boolean(const Json& value) {
  require(value.is_boolean(), "boolean device state required");
  return value.get<bool>();
}

bool uuid(const std::string& value) {
  if (value.size() != 36) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const bool separator = index == 8 || index == 13 || index == 18 || index == 23;
    if (separator ? value[index] != '-' :
        !((value[index] >= '0' && value[index] <= '9') ||
          (value[index] >= 'a' && value[index] <= 'f'))) return false;
  }
  return true;
}

bool digest_text(const std::string& value) {
  return value.size() == 64 && value.find_first_not_of("0123456789abcdef") == std::string::npos;
}

std::string sha256(const std::string& value) {
  unsigned char output[EVP_MAX_MD_SIZE];
  unsigned int length = 0;
  require(EVP_Digest(value.data(), value.size(), output, &length, EVP_sha256(), nullptr) == 1
              && length == 32, "configuration digest failed");
  std::ostringstream result;
  result << std::hex << std::setfill('0');
  for (unsigned int index = 0; index < length; ++index)
    result << std::setw(2) << static_cast<unsigned int>(output[index]);
  return result.str();
}

std::string boot_clock() {
  auto descriptor = open_path("/proc/sys/kernel/random/boot_id", O_RDONLY);
  auto boot = bounded_read(descriptor.get());
  while (!boot.empty() && (boot.back() == '\n' || boot.back() == '\r')) boot.pop_back();
  require(uuid(boot), "kernel boot identity differs");
  return "linux-boottime/" + boot;
}

Json now(const std::string& clock) {
  struct timespec value {};
  require(::clock_gettime(CLOCK_BOOTTIME, &value) == 0 && value.tv_sec >= 0,
          "CLOCK_BOOTTIME unavailable");
  const auto ticks = static_cast<std::uint64_t>(value.tv_sec) * 1'000'000'000ULL +
                     static_cast<std::uint64_t>(value.tv_nsec);
  return {{"clock_id", clock}, {"ticks_ns", std::to_string(ticks)}};
}

void validate_config(const Json& config) {
  keys(config, {"schema", "environment", "state_directory", "material_models", "robot_id",
                "new_material_channel", "other_channel", "shelf_id", "vision_id", "ft_id"});
  require(config.at("schema") == "rx.material-alignment-simulation.v1" &&
              config.at("environment") == "FILE_SIMULATION", "simulation configuration required");
  require(config.at("new_material_channel") != config.at("other_channel"),
          "two distinct channels required");
  require(config.at("material_models").is_array() && !config.at("material_models").empty(),
          "material model identities required");
  for (const auto& model : config.at("material_models"))
    require(!text(model).empty(), "material model identity required");
  for (const char* key : {"robot_id", "new_material_channel", "other_channel", "shelf_id",
                          "vision_id", "ft_id"})
    require(!text(config.at(key)).empty(), "equipment identity required");
}

bool no_native_owner(int native_root) {
  // Mirror the existing SDK snapshot's passive ownership test. A completed
  // request directory by itself is not a live command and never grants custody.
  const int duplicate = ::dup(native_root);
  require(duplicate >= 0, "native directory inspection failed");
  DIR* directory = ::fdopendir(duplicate);
  if (directory == nullptr) {
    ::close(duplicate);
    throw std::runtime_error("native directory inspection failed");
  }
  bool clear = true;
  try {
    while (true) {
      errno = 0;
      const auto* entry = ::readdir(directory);
      if (entry == nullptr) {
        require(errno == 0, "native directory inspection failed");
        break;
      }
      const std::string name(entry->d_name);
      if (name == "." || name == "..") continue;
      struct stat info {};
      require(::fstatat(native_root, name.c_str(), &info, AT_SYMLINK_NOFOLLOW) == 0,
              "native ownership entry unavailable");
      require(!S_ISLNK(info.st_mode), "native ownership symlink refused");
      if (!S_ISDIR(info.st_mode)) continue;
      require(info.st_uid == ::getuid(), "native ownership directory owner differs");
      Descriptor operation(::openat(native_root, name.c_str(),
                                    O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC));
      Descriptor lock(::openat(operation.get(), "owner.lock", O_RDONLY | O_NOFOLLOW | O_CLOEXEC));
      owned_regular(lock.get());
      if (::flock(lock.get(), LOCK_EX | LOCK_NB) != 0) {
        require(errno == EWOULDBLOCK || errno == EAGAIN, "native owner lock inspection failed");
        clear = false;
      }
    }
  } catch (...) {
    ::closedir(directory);
    throw;
  }
  ::closedir(directory);
  return clear;
}

Json observe(const std::string& config_path, const std::string& native_directory) {
  auto native_root = owned_directory(native_directory);
  const auto request = parse(bounded_read(STDIN_FILENO));
  keys(request, {"schema", "challenge", "profile_digest", "device_session", "now",
                 "dispatch", "sources"});
  require(request.at("schema") == "rx.external-process-channel.v1" &&
              request.at("dispatch").is_null(), "passive observation request required");
  require(uuid(text(request.at("challenge"))) && uuid(text(request.at("device_session"))) &&
              digest_text(text(request.at("profile_digest"))), "native identity shape differs");
  require(read_owned_at(native_root.get(), "device-session") == text(request.at("device_session")),
          "native device session differs");
  const auto clock = boot_clock();
  keys(request.at("now"), {"clock_id", "ticks_ns"});
  require(request.at("now").at("clock_id") == clock, "native clock differs");
  const auto request_ticks = text(request.at("now").at("ticks_ns"));
  require(!request_ticks.empty() && request_ticks.size() <= 20 &&
              request_ticks.find_first_not_of("0123456789") == std::string::npos &&
              (request_ticks.size() == 1 || request_ticks.front() != '0'), "native time shape differs");
  require(request.at("sources").is_array() && request.at("sources").size() <= 64,
          "bounded source list required");
  const std::set<std::string> known = {"ready", "sim/ready", "shelf.occupied", "shelf.stopped",
      "gripper.part_held", "ft.part_seated", "vision.result_available", "vision.groove_detected"};
  std::set<std::string> selected;
  for (const auto& source : request.at("sources")) {
    const auto name = text(source);
    require(known.count(name) && selected.insert(name).second, "undeclared or duplicate source");
  }
  const auto config = parse(read_owned(config_path));
  validate_config(config);
  auto state_root = owned_directory(text(config.at("state_directory")));
  const auto raw = read_owned_at(state_root.get(), "state.json");
  const auto acquired_at = now(clock);  // Timestamp this actual completed file-device read.
  const auto state = parse(raw);
  require(state.at("schema") == "rx.material-alignment-state.v1" &&
              state.at("environment") == "FILE_SIMULATION" &&
              state.at("configuration_digest") == sha256(config.dump()), "scene identity differs");
  const bool complete = state.at("pending").is_null();
  const bool occupied = boolean(state.at("shelf_occupied"));
  const bool stopped = boolean(state.at("shelf_stopped"));
  const bool held = boolean(state.at("channels").at(text(config.at("new_material_channel"))).at("holding"));
  const auto& ft = state.at("ft");
  const auto& groove = state.at("groove");
  const bool seated = !ft.is_null() && boolean(ft.at("seated"));
  const bool available = !groove.is_null();
  const bool detected = available && boolean(groove.at("found"));
  const Json values = {{"ready", complete}, {"sim/ready", complete}, {"shelf.occupied", occupied},
      {"shelf.stopped", stopped}, {"gripper.part_held", held}, {"ft.part_seated", seated},
      {"vision.result_available", available}, {"vision.groove_detected", detected}};
  Json samples = Json::object();
  for (const auto& source : selected) {
    samples[source] = {{"value", {{"boolean", values.at(source)}}}, {"acquired_at", acquired_at},
        {"uncertainty_ns", "0"}, {"quality_good", true}, {"origin_age_bounded", true}};
  }
  const bool owner_clear = no_native_owner(native_root.get());
  const bool stable = occupied || held;
  return {{"schema", "rx.external-native-snapshot.v1"}, {"challenge", request.at("challenge")},
      {"profile_digest", request.at("profile_digest")}, {"device_session", request.at("device_session")},
      {"observed_at", acquired_at}, {"uncertainty_ns", "0"},
      {"no_pending_commands", complete && owner_clear}, {"control_available", complete},
      {"support_stable", stable}, {"safe_to_drop", complete && stable && stopped}, {"samples", samples}};
}
}  // namespace

int main(int argc, char** argv) {
  try {
    require(argc == 11 && std::string(argv[1]) == "--python" && std::string(argv[3]) == "--adapter"
                && std::string(argv[5]) == "--config" && std::string(argv[7]) == "--sdk",
            "fixed installed arguments and Host-owned mode/directory required");
    for (int index : {2, 4, 6, 8, 10})
      require(argv[index][0] == '/', "absolute installed arguments required");
    const std::string mode(argv[9]);
    if (mode == "execute" || mode == "lookup") {
      // No stdin read, subprocess, rewritten payload, new process group, or retry.
      // execv preserves the original Host-owned PID and descriptors for the SDK.
      std::vector<std::string> arguments = {argv[2], "-I", "-S", "-B", argv[4],
          "--config", argv[6], "--sdk", argv[8], mode, argv[10]};
      std::vector<char*> pointers;
      for (auto& argument : arguments) pointers.push_back(argument.data());
      pointers.push_back(nullptr);
      ::execv(argv[2], pointers.data());
      throw std::runtime_error("pinned Python delegation failed");
    }
    require(mode == "observe", "unsupported Host-owned mode");
    const auto result = observe(argv[6], argv[10]);
    std::cout << result.dump();
    std::cout.flush();
    require(std::cout.good(), "native snapshot write failed");
    return 0;
  } catch (const std::exception&) {
    // Do not expose request/state contents or installation credentials in diagnostics.
    std::cerr << "material-alignment passive observer refused invalid/unavailable input\n";
    return 2;
  }
}
