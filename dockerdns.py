import docker
import dns.query
import dns.tsigkeyring
import dns.update
import sys
from pyparsing import *

LBRACE, RBRACE, SEMI, QUOTE = map(Suppress, '{};"')
algostmt="algorithm"+Word(alphanums+'-')+SEMI
secretstmt="secret"+QuotedString('"')+SEMI
keyStatement=(algostmt|secretstmt)
keyDef= ("key"+QuotedString('"')("keyname")+LBRACE+Dict(ZeroOrMore(Group(keyStatement))) +RBRACE)

keys={}

domain=sys.argv[2]
dnsserver=sys.argv[1]
print ("Using %s domain at %s for updates" %(domain,dnsserver))

for key in keyDef.searchString(open("/keyfile").read()):
    keys[key.keyname]= key.secret
    keyalgo=key.algorithm

print ("keys:" , ",".join(keys.keys()))

client = docker.from_env()

keyring = dns.tsigkeyring.from_text(keys)
update = dns.update.UpdateMessage(domain, keyring=keyring)

for c in client.containers.list(filters={"label":"dns","status":"running"}):
    for network in c.attrs["NetworkSettings"]["Networks"].values():
        ip=network["IPAddress"]
        break
    update.replace(c.name, 300, 'a', ip)
    print ("updating: ",c.name,ip)
    if "dns.alias" in c.labels:
        for alias in c.labels["dns.alias"].split(","):
            print ("alias: ",alias,ip)
            update.replace(alias, 300, 'a', ip)
    
response = dns.query.udp(update, dnsserver)

for event in client.events(decode=True,filters={"type":"container","label":"dns","event":"start"}):
    c=client.containers.get(event["id"])
    update = dns.update.UpdateMessage('vpn.phadric.de', keyring=keyring)
    for network in c.attrs["NetworkSettings"]["Networks"].values():
        ip=network["IPAddress"]
        break
    update.replace(c.name, 300, 'a', ip)
    print ("updating: ",c.name,ip)
    if "dns.alias" in c.labels:
        for alias in c.labels["dns.alias"].split(","):
            print ("alias: ",alias,ip)
            update.replace(alias, 300, 'a', ip)
    response = dns.query.udp(update, dnsserver)
    
