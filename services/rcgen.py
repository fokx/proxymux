# use rcgen to generate key-cer pair LOCALLY
import shlex
import string
import random
from subprocess import Popen, PIPE


def gen_key_cer(hostname):
  p = Popen(shlex.split(
    f'/f/rcgen/target/release/rcgen_given_name {hostname}'), stdout=PIPE, stderr=PIPE)
  out, err = p.communicate()
  assert len(err) == 0, f'err generate cer: {err}'
  cer, key = out.decode().strip().split('\n\n')
  return cer, key
def gen_xr_private_public_key_strs():
  p = Popen(shlex.split(
    f'xray x25519'), stdout=PIPE, stderr=PIPE)
  out, err = p.communicate()
  assert len(err) == 0, f'err generate cer: {err}'
  private, public = out.decode().strip().split('\n')
  private = private.split(':')[1].strip()
  public = public.split(':')[1].strip()
  return private, public

def gen_short_ids(length: int):
  assert length > 0
  def gen_short_id(length: int):
    pool  = string.digits + 'abcdef'
    res = [random.choice(pool) for _ in range(length)]
    return ''.join(res)
  res = [gen_short_id(8) for _ in range(length)]
  return res

# if __name__ == '__main__':
#   print(gen_short_ids(4))