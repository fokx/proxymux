# use rcgen to generate key-cer pair LOCALLY
import shlex
from subprocess import Popen, PIPE


def gen_key_cer(hostname):
  p = Popen(shlex.split(
    f'/f/rcgen/target/release/rcgen_given_name {hostname}'), stdout=PIPE, stderr=PIPE)
  out, err = p.communicate()
  assert len(err) == 0, f'err generate cer: {err}'
  cer, key = out.decode().strip().split('\n\n')
  return cer, key
