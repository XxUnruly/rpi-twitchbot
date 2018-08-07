#!/usr/bin/env python2

import requests
import socket
import thread
import time
import re
import cfg

def get_ops():
    req = requests.get("https://tmi.twitch.tv/group/user/turbokurt/chatters")
    if req.status_code != 200: return
    data = req.json()
    cfg.OPS.clear()
    for m in data["chatters"]["moderators"]: cfg.OPS[m] = "mod"
    for g in data["chatters"]["global_mods"]: cfg.OPS[g] = "glb"
    for a in data["chatters"]["admins"]: cfg.OPS[a] = "adm"
    for s in data["chatters"]["staff"]: cfg.OPS[s] = "stf"

def turn_on_led(args):
    print "Turning on led"

def turn_off_led(args):
    print "Turning off led"

def parse_command(args):
    cmd = args[0]
    if cmd in COMMANDS: COMMANDS[cmd](args[1:])

def is_command(s):
    return s[0] == "!"

def is_mod(u):
    return u in cfg.OPS and cfg.OPS[u] == "mod"

def chat(sock, msg):
    sock.send("PRIVMSG {} :{}\r\n".format(cfg.CHAN, msg).encode("utf-8"))

COMMANDS = {
    "turnon": turn_on_led, 
    "turnoff": turn_off_led
}

def main():
    re_privmsg = re.compile(r"^:(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)")
    buffer = ""
    s = socket.socket()
    s.connect((cfg.HOST, cfg.PORT))
    s.send("PASS {}\r\n".format(cfg.PASS).encode("utf-8"))
    s.send("NICK {}\r\n".format(cfg.NICK).encode("utf-8"))
    s.send("JOIN {}\r\n".format(cfg.CHAN).encode("utf-8"))
    
    thread.start_new_thread(get_ops, ())
    
    print "--- Bot started"
    
    while True:
        # Get 1024 bytes from stream chat, might contain one or more messages.
        buffer += s.recv(1024).decode("utf-8")
        # Split buffer on newlines to get all messages. 
        temp = buffer.split("\r\n")
        # The last element in the split will not necessarily make up a full 
        # message, so it will be the new buffer.
        buffer = temp.pop()
        
        for line in temp:
            print line
            if line == "PING :tmi.twitch.tv":
                s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            if line.find("PRIVMSG") != -1:
                match = re_privmsg.match(line)
                usr = match.group(1)
                msg = match.group(2).lower()
                if is_command(msg):
                    if is_mod(usr): parse_command([x.lower() for x in msg[1:].split(" ")])
                    else: chat(s, "@{} You do not have the permissions to justify this command.".format(usr))
        

if __name__ == "__main__":
    main()
