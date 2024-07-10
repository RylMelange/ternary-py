
class Circuit():
    def __init__(self, gates):
        self.gates = gates
        self.gatelist = gates.keys()
        self.tasklist = []
        self.custom = {}

    def process(self):
        if not self.tasklist:
            self.update_gate(self.gates[0])
        
        counter = 0
        while self.tasklist:
            self.update_gate(self.gates[self.tasklist[0]])
            self.tasklist.pop(0)

            counter += 1
            if counter >100:
                print("depth reached")
                break
        
    def update_gate(self, component):
        gate,inputs,destinations = component
        match gate:
            case "input":
                size = len(inputs)
                outputs = [None] * size
                for i in range(size):
                    outputs[i] = inputs[i]
            case "neg":
                outputs = [inputs[0]*-1]
            case "max":
                outputs = [max(inputs[0],inputs[1])]          
            case "min":
                outputs = [min(inputs[0],inputs[1])]          
            case "split":
                outputs = [inputs[0]] * len(destinations)
            case "out":
                outputs = []
                print(outputs)
            case other:
                if gate in custom_gates:
                    inputstring = ''
                    for input in inputs:
                        match input:
                            case 1:
                                inputstring += '+'
                            case -1:
                                inputstring += '-'
                            case 0:
                                inputstring += '0'
                    outputs = custom_gates[gate][inputstring]

                else:
                    print(f"gate {gate} not found")
                    print("finding gates from file not implemented")
                    exit()

        for i in range(len(outputs)):
            destination = destinations[i]
            value = outputs[i]

            if self.gates[destination[0]][1][destination[1]] == value:
                continue
            else:
                self.gates[destination[0]][1][destination[1]] = value
            if destination[0] not in self.tasklist:
                self.tasklist.append(destination[0])

#'''
#  id: [type,       inputs, outputs         ]
gates_mul = {
    0: ["input",    [1,0],  [(1,0),(2,0)]   ],
    1: ["split",    [2],    [(3,0),(4,0)]   ],
    2: ["split",    [2],    [(3,1),(4,1)]   ],
    3: ["min",      [2,2],  [(6,0)]         ],
    4: ["max",      [2,2],  [(5,0)]         ],
    5: ["neg",      [2],    [(6,1)]         ],
    6: ["max",      [2,2],  [(-1,0)]        ],
    -1:["out",      [2],    []              ]
    }
custom_gates = {
    "pos": {'0':[1],'+':[1],'-':[2]}
}

circuitA = Circuit(gates_mul)
circuitA.process()
print(circuitA.gates)
#'''
