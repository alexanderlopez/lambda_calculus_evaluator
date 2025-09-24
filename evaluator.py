import sys
import copy

class LambdaTerm:
    def __init__(self, lambdaType, data):
        self.lambdaType = lambdaType
        match self.lambdaType:
            case 0:
                # variable
                self.symbol = data
            case 1:
                # Function declaration
                self.boundVariable = data[0]
                self.innerExpression = data[1]
            case 2:
                # application
                self.leftExpression = data[0]
                self.rightExpression = data[1]
            case _:
                # error
                print("Error: Undefined Expression Type", file=sys.stderr)

    def pretty(self):
        match self.lambdaType:
            case 0:
                return self.symbol
            case 1:
                return f'λ{self.boundVariable}.{self.innerExpression.pretty()}'
            case 2:
                match (self.leftExpression.lambdaType, self.rightExpression.lambdaType):
                    case (0, 0):
                        return f'{self.leftExpression.pretty()} {self.rightExpression.pretty()}'
                    case (0, 1):
                        return f'{self.leftExpression.pretty()} ({self.rightExpression.pretty()})'
                    case (0, 2):
                        return f'{self.leftExpression.pretty()} ({self.rightExpression.pretty()})'
                    case (1, 0):
                        return f'({self.leftExpression.pretty()}) {self.rightExpression.pretty()}'
                    case (1, 1):
                        return f'({self.leftExpression.pretty()}) ({self.rightExpression.pretty()})'
                    case (1, 2):
                        return f'({self.leftExpression.pretty()}) ({self.rightExpression.pretty()})'
                    case (2, 0):
                        return f'{self.leftExpression.pretty()} {self.rightExpression.pretty()}'
                    case (2, 1):
                        return f'{self.leftExpression.pretty()} ({self.rightExpression.pretty()})'
                    case (2, 2):
                        return f'{self.leftExpression.pretty()} ({self.rightExpression.pretty()})'

    def __str__(self):
        typeStr = ""
        match self.lambdaType:
            case 0:
                typeStr = "var"
            case 1:
                typeStr = "fun"
            case 2:
                typeStr = "appl"

        objectStr = f"(T:{typeStr}"

        addLines = []
        
        match self.lambdaType:
            case 0:
                objectStr += f" N:{self.symbol}"
            case 1:
                addLines.append((f"V: {self.boundVariable}", 1))
                addLines.append(("I:\n", 1))
                addLines += [(a, 2) for a in str(self.innerExpression).splitlines(keepends=True)]
            case 2:
                addLines.append(("\n", 0))
                addLines.append(("L:\n", 1))
                addLines += [(a, 2) for a in str(self.leftExpression).splitlines(keepends=True)]
                addLines.append(("\n", 0))
                addLines.append(("R:\n", 1))
                addLines += [(a, 2) for a in str(self.rightExpression).splitlines(keepends=True)]

        for line in addLines:
            objectStr += "  " * line[1] + line[0]

        if objectStr[-1] == "\n":
            objectStr = objectStr[:-1] + ")\n"
        else:
            objectStr += ")"

        return objectStr

    def freeVars(self):
        match self.lambdaType:
            case 0:
                return set([self.symbol])
            case 1:
                innerFreeVar = self.innerExpression.freeVars()
                innerFreeVar.discard(self.boundVariable)
                return innerFreeVar
            case 2:
                return (self.leftExpression.freeVars() | self.rightExpression.freeVars())

    def rename(self, originalVar, newVar):
        match self.lambdaType:
            case 0:
                if self.symbol == originalVar:
                    self.symbol = newVar
            case 1:
                if self.boundVariable == newVar:
                    self.boundVariable += '0'
                    self.innerExpression.rename(newVar, self.boundVariable)
                self.innerExpression.rename(originalVar, newVar)
            case 2:
                self.leftExpression.rename(originalVar, newVar)
                self.rightExpression.rename(originalVar, newVar)

    def replace(self, variable, lambdaExpr):
        if not variable in self.freeVars():
            return self

        match self.lambdaType:
            case 0:
                if self.symbol == variable:
                    return copy.deepcopy(lambdaExpr)
            case 1:
                replaceFreeVars = lambdaExpr.freeVars()
                if self.boundVariable in replaceFreeVars:
                    oldBoundVar = self.boundVariable
                    while self.boundVariable in replaceFreeVars:
                        self.boundVariable += '0'

                    self.innerExpression.rename(oldBoundVar, self.boundVariable)
                self.innerExpression = self.innerExpression.replace(variable, lambdaExpr)
                return self
            case 2:
                self.leftExpression = self.leftExpression.replace(variable, lambdaExpr)
                self.rightExpression = self.rightExpression.replace(variable, lambdaExpr)
                return self

    def outerEvalStep(self):
        match self.lambdaType:
            case 0:
                return (self, False)
            case 1:
                (self.innerExpression, change) = self.innerExpression.outerEvalStep()
                return (self, change)
            case 2:
                if self.leftExpression.lambdaType == 1:
                    return (self.leftExpression.innerExpression.replace(self.leftExpression.boundVariable,
                                                                self.rightExpression), True)
                else:
                    (self.leftExpression, change) = self.leftExpression.outerEvalStep()

                    if not change:
                        (self.rightExpression, rchange) = self.rightExpression.outerEvalStep()
                        return (self, rchange)

                    return (self, change)

def getSpace(string):
    strlen = len(string)
    depth = 0
    for x in range(1, strlen + 1):
        curChar = string[strlen - x]
        
        match curChar:
            case ')':
                depth += 1
            case '(':
                depth -= 1
            case ' ':
                if depth == 0:
                    return (strlen - x)

    return -1

def mustTrim(string):
    if string[0] != '(':
        return False

    depth = 0

    for x in range(len(string) - 1):
        curChar = string[x]
        match curChar:
            case '(':
                depth += 1
            case ')':
                depth -= 1

        if depth == 0:
            return False

    return True

def parseExpression(string, dictionary):
    if mustTrim(string):
        string = string[1:-1]

    if string[0] == 'λ':
        varEnd = string.find('.')
        variable = string[1:varEnd]
        defString = string[varEnd + 1:]
        return LambdaTerm(1, [variable, parseExpression(defString, dictionary)])

    if string.find(' ') == -1:
        if string in dictionary:
            return parseExpression(dictionary[string], dictionary)
        elif string.isdigit():
            church_numeral = 'λf.λx.'
            for x in range(int(string)):
                church_numeral += 'f ('
            church_numeral += 'x'
            for x in range(int(string)):
                church_numeral += ')'
            return parseExpression(church_numeral, dictionary)
        else:
            return LambdaTerm(0, string)

    # split into outer tokens that skip round brackets.
    # we must be in an application
    splitSpace = getSpace(string)
    leftExpr = string[:splitSpace]
    rightExpr = string[splitSpace+1:]
    return LambdaTerm(2, [parseExpression(leftExpr, dictionary), parseExpression(rightExpr, dictionary)])

def loopEval(lambdaExpr):
    result = lambdaExpr.outerEvalStep()
    while result[1]:
        result = result[0].outerEvalStep()
    print(result[0].pretty())

if __name__ == '__main__':
    replaceDict = dict()
    expression = ''
    if len(sys.argv) == 3:
        expression = sys.argv[2]
        mappingFile = open(sys.argv[1], 'rt')
        currentLine = mappingFile.readline().strip()
        while currentLine != '':
            splitLine = currentLine.split(':')
            replaceDict[splitLine[0]] = splitLine[1]
            currentLine = mappingFile.readline().strip()
        mappingFile.close()
    else:
        expression = sys.argv[1]

    lambdaExpr = parseExpression(expression, replaceDict)
    print(lambdaExpr.pretty())
    result = (lambdaExpr, False)
