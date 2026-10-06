#!/usr/bin/env python3
"""Fresh Linux CI SDK consumer. Downloads artifacts only; never checks out RX core."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from artifacts import sha,verify_checksums,extract_new,inventory

CMAKE='''cmake_minimum_required(VERSION 3.22)
project(rx_sdk_only_consumer LANGUAGES CXX)
find_package(rxclcpp CONFIG REQUIRED)
add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE rxclcpp::rxclcpp)
target_compile_options(consumer PRIVATE -Wall -Wextra -Werror)
'''
CPP='''#include <rxclcpp/wire.hpp>
#include <rx/contract/v1/contract.pb.h>
#include <iostream>
int main() {
  rx::contract::v1::PeerHello value;
  auto result = rxclcpp::wire::parse(value, std::string("\\xff", 1));
  if (result.code != rxclcpp::wire::Code::INVALID_ARGUMENT) return 1;
  std::cout << "installed-public-header-link-and-strict-rejection\\n";
}
'''


def run(args,root,label,env=None):
    result=subprocess.run(list(map(str,args)),cwd=root,env=env,capture_output=True,text=True)
    (root/(label+'.stdout')).write_text(result.stdout);(root/(label+'.stderr')).write_text(result.stderr)
    if result.returncode:raise RuntimeError(label+' failed; see retained logs')
    return result.stdout


def compare_corpus(python,cpp):
    a=python['cases'];b=cpp['cases']
    if not a or a!=b or any(x['actual']!=x['expected'] or x.get('roundtrip_actual')!=x.get('roundtrip_expected') for x in a):
        raise ValueError('released client corpus differs or contains a failure')
    return len(a)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifacts',type=Path,required=True)
    p.add_argument('--expected-checksums-sha256',required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--execute-fresh-linux-ci',action='store_true');a=p.parse_args()
    if not a.execute_fresh_linux_ci or sys.platform!='linux' or os.environ.get('CI')!='true':
        p.error('only explicitly selected fresh Linux CI may execute this consumer')
    root=a.artifacts.resolve(strict=True);work=a.work.resolve()
    if work.is_relative_to(root) or root.is_relative_to(work):raise ValueError('immutable artifacts and work must be disjoint')
    for item in root.rglob('*'):
        if item.name=='.git' or item.name in ('rx-platform','rx-solutions'):
            raise ValueError('core checkout/source is not a consumer input')
    raw=(root/'CHECKSUMS.sha256').read_bytes()
    if sha(raw)!=a.expected_checksums_sha256:raise ValueError('selected artifact checksums differ')
    entries=verify_checksums(root,raw,allowed_extras=('CHECKSUMS.sha256',))
    before=inventory(root);work.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1')
    env.pop('PYTHONPATH',None);env.pop('CMAKE_PREFIX_PATH',None);env.pop('LD_LIBRARY_PATH',None)
    wheelhouse=extract_new(root/'python-wheelhouse.tar.gz',work/'wheel-extracted','python-wheelhouse')
    cpp=extract_new(root/'rxclcpp.tar.gz',work/'cpp-extracted','rxclcpp')
    adapter=extract_new(root/'external-adapter-sdk.tar.gz',work/'adapter-extracted','external-adapter-sdk')
    wheels=list(root.glob('rxclpy-*.whl'))
    if len(wheels)!=1:raise ValueError('exactly one selected rxclpy wheel required')
    run([sys.executable,'-m','venv',work/'venv'],work,'venv',env)
    python=work/'venv/bin/python'
    run([python,'-I','-m','pip','install','--no-index','--find-links',wheelhouse,wheels[0]],work,'offline-wheel-install',env)
    pyresult=json.loads(run([python,'-I','-m','rxclpy.conformance'],work,'python-corpus',env))
    libraries=sorted({str(x.parent) for x in cpp.rglob('librxclcpp.so*')})
    if not libraries:raise ValueError('installed SDK shared library absent')
    env['LD_LIBRARY_PATH']=':'.join(libraries)
    corpus=cpp/'share/rxclcpp/protocol/strict-wire-v1/vectors.json'
    cppresult=json.loads(run([cpp/'bin/rxclcpp-conformance',corpus],work,'cpp-corpus',env))
    count=compare_corpus(pyresult,cppresult)
    project=work/'consumer';project.mkdir();(project/'CMakeLists.txt').write_text(CMAKE);(project/'main.cpp').write_text(CPP)
    run(['cmake','-S',project,'-B',work/'consumer-build','-DCMAKE_PREFIX_PATH='+str(cpp)],work,'cmake-configure',env)
    run(['cmake','--build',work/'consumer-build','--parallel','1'],work,'cmake-build',env)
    run([work/'consumer-build/consumer'],work,'cpp-consumer',env)
    run([python,'-I','-B',adapter/'conformance.py','--sdk',adapter,'--output',work/'adapter-evidence','--execute-fresh-linux-ci'],work,'native-helper-component',env)
    rust=extract_new(root/'public-rust-contracts.tar.gz',work/'rust-extracted','public-rust-contracts')
    locks=(rust/'Cargo.lock').read_bytes();env['CARGO_TARGET_DIR']=str(work/'rust-target');env['CARGO_BUILD_JOBS']='1'
    # Only the declared public contract SDK source is available, not core crates.
    run(['cargo','fetch','--manifest-path',rust/'Cargo.toml','--locked'],work,'public-contract-fetch',env)
    run(['cargo','check','--manifest-path',rust/'Cargo.toml','--locked','--offline','--workspace'],work,'public-contract-compile',env)
    if (rust/'Cargo.lock').read_bytes()!=locks:raise ValueError('consumer changed SDK dependency lock')
    if inventory(root)!=before:raise ValueError('consumer modified immutable delivered artifact inputs')
    result={'schema':'rx.m5.sdk-consumer.v1','status':'PASS_FOR_SDK_CONSUMER_SCOPE','checksums_sha256':sha(raw),
        'artifacts':entries,'source_checkout_present':False,'corpus_cases':count,'python_offline_install':True,
        'cpp_installed_config_consumer':True,'public_rust_contract_source_bundle_compiles':True,
        'external_helper_component':json.loads((work/'adapter-evidence/result.json').read_text()),
        'limits':['No registered Run evidence in this result; full_run is a separate required gate.',
            'CHECKSUMS integrity is not publisher provenance until the separate trusted OpenPGP check succeeds.',
            'Public Rust contract source is explicitly included; core authority/runtime source is absent.']}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'corpus_cases':count}))


if __name__=='__main__':main()
