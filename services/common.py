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

# potentially occupied ports:
# ANY_P1 - ANY_P2
# HY_P3 - HY_P5

HY_P1 = 360
HY_P2 = 442
HY_P3 = 444
HY_P4 = 514
HY_P5 = 650

TUIC_P1 = HY_P5 + 1
TUIC_P2 = 733

NAIVE_P1 = TUIC_P2  + 1
NAIVE_P2 = 811

XR_P1 = NAIVE_P2 + 1
XR_P2 = 900
