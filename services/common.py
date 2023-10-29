masquerade_domain_pool = '''
www.oracle.com
yandex.ru
live.com
docomo.ne.jp
office.com
microsoftonline.com
bing.com
zoom.us
fandom.com
stackoverflow.com
nginx.org
nginx.org
www.cloudflare.com

'''.strip().splitlines()

HY_P1 = 201
HY_P2 = 442
HY_P3 = 444
HY_P4 = 614
HY_P5 = 890

# potentially occupied ports:
# HY_P1-HY_P2, HY_P3-HY_P5
# TUIC_P1-TUIC_P2

TUIC_P1 = 891
TUIC_P2 = 1023