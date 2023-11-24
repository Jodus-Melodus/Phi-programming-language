from backend.values import *
from time import time, sleep
import sys

def out(arg) -> str|bool:
    if isinstance(arg, (numberValue, stringValue, booleanValue, nullValue)):
        return arg.value
    elif isinstance(arg, objectValue):
        res = '{'
        for prop in arg.properties:
            res += f"{out(prop)} : {out(arg.properties[prop])}, "
        return res + '}'
    elif isinstance(arg, arrayValue):
        res = '['
        for item in arg.items:
            res += str(out(item)) + ', '
        return res + ']'
    elif isinstance(arg, function):
        return f"fn {arg.name}()"
    else:
        return arg

def length(arg) -> numberValue:
    if isinstance(arg, objectValue):
        return numberValue(len(arg.properties))
    elif isinstance(arg, arrayValue):
        return numberValue(len(arg.items))

def in_(arg:stringValue) -> stringValue:
    sys.stdout.write(arg.value)
    return stringValue(sys.stdin.readline().strip())

def now() -> numberValue:
    return numberValue(time())

def type_(arg:RuntimeValue) -> str:
    return arg.type
    
def wait(seconds) -> None:
    sleep(int(seconds.value))

def root(radicand, index) -> numberValue:
    return numberValue(float(float(radicand.value))**(1/float(index.value)))
