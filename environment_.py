from errors import nameError, syntaxError
from values import *
import builtInFunctions as bif

class environment:
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.variables = {}
        self.constants = {}

    def __repr__(self) -> str:
        return str({
            "parent":self.parent,
            "variables":self.variables
        })

    def assignVariable(self, varName: str, varValue) -> None:
        if varName in self.variables:
            self.variables[varName] = varValue
        elif varName in self.constants:
            syntaxError("Can't assign a new value to a constant")
        else:
            nameError(varName)

        return varValue

    def declareVariable(self, varName: str, varValue, constant:bool=False) -> None:
        if (varName in self.variables) or (varName in self.constants):
            syntaxError(f"Variable {varName} already defined.")
        else:
            if constant:
                self.constants[varName] = varValue
            else:
                self.variables[varName] = varValue

        return varValue

    def lookup(self, varName: str) -> None:
        env = self.resolve(varName)
        if varName in self.constants:
            return env.constants[varName]
        else:
            return env.variables[varName]

    def resolve(self, varName: str) -> None:
        if varName in self.variables:
            return self
        elif varName in self.constants:
            return self
        if self.parent == None:
            nameError(varName)

        return self.parent.resolve(varName)

def createGlobalEnvironment() -> environment:
    env = environment()
    # functions
    env.declareVariable('disp', nativeFunction(lambda args, scope : print(bif.disp(args[0]))), True)
    env.declareVariable('now', nativeFunction(lambda args, scope : bif.now()), True)
    env.declareVariable('wait', nativeFunction(lambda args, scope : bif.wait(args[0])), True)
    env.declareVariable('type', nativeFunction(lambda args, scope : bif.type_(args[0])), True)
    env.declareVariable('root', nativeFunction(lambda args, scope : bif.root(args[0], args[1])), True)

    # variables
    env.declareVariable('_', nullValue(), True)
    env.declareVariable('T', booleanValue(True), True)
    env.declareVariable('F', booleanValue(False), True)
    
    return env