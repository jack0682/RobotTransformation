"""Trusted CI provisioning and installed-command transport. Imported only by CI runner."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.parse
import uuid
from fixtures import encoded


def read(path): return json.loads(Path(path).read_bytes())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = encoded(value)
    if path.exists() and path.read_bytes() != raw:
        raise ValueError('Refusing to overwrite an original document: ' + str(path))
    if not path.exists(): path.write_bytes(raw)
    return path


def replace_configuration(path, value):
    """Provisioning only, before first Host init; callers retain before/after pins."""
    Path(path).write_bytes(encoded(value))


def checked(args):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True)
    if result.returncode: raise RuntimeError(f'{args[:2]} failed: {result.stderr[-3000:]}')
    return result.stdout


class Signer:
    def __init__(self, root):
        self.root = root
        root.mkdir(mode=0o700)
        self.keys = {}
        for role in ['package', 'review', 'qualification']:
            private, public = root/(role+'.pem'), root/(role+'.der')
            checked(['openssl', 'genpkey', '-algorithm', 'ED25519', '-out', private])
            checked(['openssl', 'pkey', '-in', private, '-pubout', '-outform', 'DER', '-out', public])
            raw = public.read_bytes()
            if len(raw) != 44 or raw[:12].hex() != '302a300506032b6570032100':
                raise ValueError('Ed25519 encoding differs')
            self.keys['delivery-'+role+'-signer'] = (private, raw[-32:].hex())

    def sign(self, request, destination):
        value = read(request)
        raw = bytes.fromhex(value['message_hex'])
        if 'message_digest' in value and hashlib.sha256(raw).hexdigest() != value['message_digest']:
            raise ValueError('Product signing request digest differs')
        private, _ = self.keys[value['key']]
        message = self.root/(uuid.uuid4().hex+'.message')
        signature = self.root/(uuid.uuid4().hex+'.sig')
        message.write_bytes(raw)
        checked(['openssl', 'pkeyutl', '-sign', '-rawin', '-inkey', private, '-in', message, '-out', signature])
        write(destination, {'key': value['key'], 'signature': signature.read_bytes().hex()})

    def rekey_seed(self, seed):
        policy, manifest, fixtures = [read(seed/name) for name in ['package-policy.json','seed.json','signing-fixtures.json']]
        for key in fixtures['keys']:
            private, public = self.keys[key['id']]
            der = self.root/(key['id']+'.pkcs8')
            checked(['openssl', 'pkey', '-in', private, '-outform', 'DER', '-out', der])
            raw = der.read_bytes()
            if len(raw) != 48 or raw[:16].hex() != '302e020100300506032b657004220420':
                raise ValueError('Ed25519 PKCS8 seed encoding differs')
            key.update(private_seed_hex=raw[-32:].hex(), public_key=public)
            manifest['public_signers'][key['id']] = public
        for key in policy['keys']: key['verifying_key'] = self.keys[key['id']][1]
        replace_configuration(seed/'package-policy.json', policy)
        manifest['package_policy_sha256'] = sha(seed/'package-policy.json')
        replace_configuration(seed/'signing-fixtures.json', fixtures)
        replace_configuration(seed/'seed.json', manifest)


def installed_materials_type(base):
    class InstalledMaterials(base):
        def configure(self, platform, signer):
            self.platform, self.signer = platform, signer

        def exporter(self, test, environment, label):
            for key, value in environment.items():
                if key not in ('RX_CELL_DELIVERY_ARCH','RX_CELL_COMPILER_ID','RX_CELL_DELIVERY_PORT','RX_CELL_QUALIFICATION_VALIDATOR_ID'):
                    if not Path(value).is_relative_to(self.temporary):
                        raise ValueError('Fixture exporter path is outside fresh private root')
            args = ['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL',
                '--security-opt','no-new-privileges','--user',f'{os.getuid()}:{os.getgid()}',
                '--tmpfs','/tmp:rw,mode=1777','-v',f'{self.temporary}:{self.temporary}:rw']
            for key, value in environment.items(): args += ['-e',key+'='+value]
            result = subprocess.run(args+['--entrypoint','/opt/rx/dev/delivery-fixture',self.platform,test,'--ignored','--exact'], capture_output=True, text=True)
            (self.evidence/(label+'.log')).write_text(result.stdout+result.stderr)
            if result.returncode or '1 passed; 0 failed' not in result.stdout:
                raise RuntimeError('Installed fixture exporter failed: '+label)

        def create_seed(self, architecture, composition_draft=None):
            if composition_draft is not None: raise ValueError('Single-node seed only')
            self.exporter('export_delivery_seed', {'RX_CELL_DELIVERY_OUTPUT':str(self.seed),
                'RX_CELL_DELIVERY_ARCH':architecture}, 'export-seed')
            self.signer.rekey_seed(self.seed)
            shutil.copytree(self.seed, self.public_seed, ignore=shutil.ignore_patterns('signing-fixtures.json'))
            self.preserve_public(self.public_seed, 'seed')
    return InstalledMaterials


def mutation_targets(command, arguments):
    """Parse every target; exec has one target followed by its inner command."""
    flags={
        'start':{'-a','--attach','-i','--interactive'},
        'stop':set(), 'restart':set(), 'kill':set(),
        'rm':{'-f','--force','-v','--volumes','-l','--link'},
        'exec':{'-i','--interactive','-t','--tty','-d','--detach'},
    }
    valued={
        'start':set(), 'stop':{'-t','--time','--timeout'},
        'restart':{'-t','--time','--timeout'}, 'kill':{'-s','--signal'},
        'rm':set(), 'exec':{'-u','--user','-w','--workdir','-e','--env'},
    }
    if command not in flags:raise ValueError('Unsupported container mutation')
    targets=[];index=0;end_options=False
    while index<len(arguments):
        token=str(arguments[index]);index+=1
        if token=='--' and not end_options:
            end_options=True;continue
        if not end_options and token.startswith('-'):
            key,separator,value=token.partition('=')
            if key in flags[command] and not separator:continue
            if key not in valued[command]:raise ValueError('Unknown Docker mutation option: '+key)
            if not separator:
                if index>=len(arguments):raise ValueError('Missing Docker option value')
                value=str(arguments[index]);index+=1
            if not value or value.startswith('-'):raise ValueError('Invalid Docker option value')
            continue
        targets.append(token)
        if command=='exec':
            if index>=len(arguments):raise ValueError('Docker exec requires an inner command')
            break
    if not targets:raise ValueError('No Docker container target')
    return targets


def owned_docker_type(base):
    class OwnedDocker(base):
        def run(self, *args, capture=True):
            if args[0] in ('exec','stop','start','restart','kill','rm'):
                names = mutation_targets(args[0], args[1:])
                if any(not n.startswith(self.prefix+'-') or n not in self.containers for n in names):
                    raise ValueError('Only this fresh run owns the target container')
            if args[0] in ('run','create'):
                args = (args[0], '--memory=2g','--cpus=2','--pids-limit=256',*args[1:])
            return super().run(*args, capture=capture)

        def put(self, image, volume, source, path='/'):
            if volume not in self.volumes: raise ValueError('Unowned target volume')
            super().put(image, volume, source, path)
            self.run('run','--rm','--network','none','--user','0','--cap-drop','ALL','--cap-add','CHOWN',
                '--cap-add','DAC_OVERRIDE','-v',volume+':/copy','--entrypoint','/bin/chown',image,'-R','10001:10001','/copy')
    return OwnedDocker


class Author:
    def __init__(self, docker, image, root, terminal, evidence):
        self.docker, self.image, self.root, self.terminal, self.evidence = docker, image, root, terminal, evidence
        self.serial = 0

    def command(self, binary, args, label, check=True, network=False, drop_stdout=False, historical_client=None):
        self.serial += 1
        name = self.docker.prefix+'-author-'+str(self.serial)
        command = ['create','--name',name,'--network','host' if network else 'none','--read-only',
            '--memory=1g','--cpus=1','--pids-limit=64','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--user',f'{os.getuid()}:{os.getgid()}','--tmpfs','/tmp:rw,mode=1777',
            '-v',str(self.root)+':/author:rw']
        if network: command += ['-v',str(self.terminal)+':/terminal:ro']
        historical_pins=None
        if historical_client is not None:
            from historical_bundle import validate_historical_bundle
            historical_client=Path(historical_client).resolve()
            historical_pins=validate_historical_bundle(historical_client.parent)
            if historical_client.name!='client':raise ValueError('Historical four-file directory required')
            command += ['-v',str(historical_client)+':/author/historical-client:ro','--env','CI=true']
        command += ['--entrypoint',binary,self.image,*map(str,args)]
        self.docker.run(*command)
        self.docker.containers.append(name)
        inspection = self.docker.state(name)
        destinations = {m['Destination']:m for m in inspection['Mounts'] if m['Type']=='bind'}
        other_mounts=[m for m in inspection['Mounts'] if m['Type']!='bind']
        wanted = {'/author':(str(self.root),True)}
        if network:wanted['/terminal']=(str(self.terminal),False)
        if historical_client is not None:wanted['/author/historical-client']=(str(historical_client),False)
        if (inspection['Image']!=self.image or not inspection['HostConfig']['ReadonlyRootfs']
                or set(destinations)!=set(wanted)
                or any(m['Type']!='tmpfs' or m['Destination']!='/tmp' for m in other_mounts)
                or any(destinations[k]['Type']!='bind' or destinations[k]['Source']!=source
                       or destinations[k]['RW']!=writable for k,(source,writable) in wanted.items())):
            raise ValueError('Actual author image/mount boundary differs')
        stem = self.evidence/(f'{self.serial:05}-'+label)
        write(stem.with_suffix('.boundary.json'), {'image':inspection['Image'],
            'mounts':inspection['Mounts'],'readonly_rootfs':inspection['HostConfig']['ReadonlyRootfs'],
            'expected_host_image':self.image,'source_mounts':[], 'signer_private_mounts':[],
            'verification_kit_mounts':[], 'registered_terminal_credentials_only':network,'historical_readonly_overlay':historical_pins})
        options = {'text':True, 'stderr':subprocess.PIPE,
                   'stdout':subprocess.DEVNULL if drop_stdout else subprocess.PIPE}
        try:
            result = subprocess.run(['docker','start','--attach',name], **options)
            stem.with_suffix('.stdout').write_text(result.stdout or '')
            stem.with_suffix('.stderr').write_text(result.stderr)
            write(stem.with_suffix('.command.json'), {'argv':['docker',*command],'returncode':result.returncode,
                  'consumer_result_stdout_discarded':drop_stdout,
                  'boundary':'installed CLI; author mount and optional registered-terminal only'})
            if check and result.returncode: raise RuntimeError(label+': '+result.stderr[-3000:])
            return result
        finally:
            self.docker.run('rm',name)
            self.docker.containers.remove(name)

    def core_identity(self, label):
        paths=['/opt/rx/bin/rx-hostd','/opt/rx/bin/rx-executor-service','/opt/rx/bin/rx-bt-engine',
               '/opt/rx/bin/rx-device-package','/opt/rx/bin/rx-process-package',
               '/opt/rx/python/python','/opt/rx/client/rx']
        code='import hashlib,json,pathlib; print(json.dumps({p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in '+repr(paths)+'}))'
        return json.loads(self.command('python3',['-c',code],label).stdout)

    def product(self, name, args, label):
        return json.loads(self.command('/opt/rx/bin/'+name,args,label).stdout)

    def cli(self, kind, args, label, who='engineer', check=True):
        result = self.command('python3',['/opt/rx/client/rx',kind,'--connection','/terminal/'+who+'.json',
            '--state-dir','/author/client/'+kind+'/'+who,*map(str,args)],label,check=check,network=True)
        return json.loads(result.stdout) if check else result

    def cp(self, relative): return '/author/'+str(relative)


class PublicApi:
    def __init__(self, author, who, rejected_type):
        self.author,self.who,self.rejected_type=author,who,rejected_type
        self.sequence=0
        self.requests={}

    def get(self, path, **query):
        if query: path += '?'+urllib.parse.urlencode(query)
        self.sequence+=1
        value = self.author.cli('api',['get',path],self.who+'-get-'+str(self.sequence),self.who,False)
        return self._decode(value)

    def post(self, label, path, body):
        if label in self.requests:
            saved = self.requests[label]
            if saved['path'] != path or saved['body'] != body: raise ValueError('Original API document changed')
        else:
            self.requests[label]={'path':path,'body':body,'id':str(uuid.uuid4())}
        saved=self.requests[label]
        name='requests/'+self.who+'/'+label+'.json'
        write(self.author.root/name,body)
        result=self.author.cli('api',['post',path,'--body',self.author.cp(name),'--request-id',saved['id']],label,self.who,False)
        return self._decode(result)

    def mutate(self,label,path,command):
        if label in self.requests: body=self.requests[label]['body']
        else: body={'request_key':str(uuid.uuid4()),'command':command}
        if body['command']!=command: raise ValueError('Original command changed')
        return self.post(label,path,body)

    def recover(self,label):
        saved=self.requests[label]
        return self.post(label,saved['path'],saved['body'])

    def _decode(self,result):
        if result.returncode:
            match=re.search(r'HTTP (\d{3})',result.stderr)
            if match: raise self.rejected_type(int(match[1]),{'stderr':result.stderr})
            raise RuntimeError(result.stderr[-3000:])
        return json.loads(result.stdout)


def connections(final, destination):
    browser=read(final/'browser-fixture.json')
    destination.mkdir(mode=0o700)
    for key,field in [('ca','ca'),('certificate','certificate'),('private_key','private_key')]:
        shutil.copyfile(final/browser[field],destination/key)
    for who,password in browser['credentials'].items():
        (destination/(who+'.password')).write_text(password)
        (destination/(who+'.password')).chmod(0o600)
        write(destination/(who+'.json'),{'schema':'rx.runtime-skill-connection.v1','origin':browser['origin'],
            'ca':'/terminal/ca','certificate':'/terminal/certificate','private_key':'/terminal/private_key',
            'principal':who,'password_file':'/terminal/'+who+'.password'})
    return browser
