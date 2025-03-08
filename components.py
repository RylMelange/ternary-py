import pygame
from data import *

global circuit

class Component:
    def __init__(self, id, argument):
        self.gate_type, values, destinations, position, *_ = argument
        self.id = id
        self.rect = pygame.Rect(position,(GATE_WIDTH, gate_styles[self.gate_type][0]))
        self.wires = []
        input_size = gate_styles[self.gate_type][1]

        self.sources = [None] * input_size
        if values != None:
            self.values = values
        else:
            self.values = [2] * input_size

        if destinations != None:
            self.destinations = destinations
        else:
            self.destinations = [None] * gate_styles[self.gate_type][2]

        if len(argument) > 4:
            self.memory = argument[4]
        else:
            if self.gate_type in ["sr_latch", "d_latch"]:
                self.memory = [0]
            elif self.gate_type in ["3reg"]:
                self.memory = [0,0,0]
            elif self.gate_type in ["3mem", "control"]:
                self.memory = {}
            else:
                self.memory = None


    def update_outports(self): #updates destination gates' sources
        for num, destination in enumerate(self.destinations):
            if destination:
                circuit[destination[0]].sources[destination[1]]= (self.id, num)

    def update_inports(self): #updates destination gates' sources
        if self.sources:
            for i in range(gate_styles[self.gate_type][1]):
                if not self.sources[i]:
                    self.sources[i] = None
        else:
            for i in range(gate_styles[self.gate_type][1]):
                self.sources.append(None)

    def update_gate(self):
        if self.id == -2:
            return
        gate_style = gate_styles[self.gate_type]
        inputs = self.values
        match self.gate_type:
            case "input":
                outputs = [None] * gate_style[1]
                for i in range(gate_style[1]):
                    outputs[i] = inputs[i]
            case "neg":
                outputs = [inputs[0]*-1]
            case "max":
                outputs = [max(inputs[0],inputs[1])]          
            case "min":
                outputs = [min(inputs[0],inputs[1])]
            case "inc":
                if inputs[0] == 1:
                    outputs = [-1]
                else:
                    outputs = [inputs[0]+1]
            case "dec":
                if inputs[0] == -1:
                    outputs = [1]
                else:
                    outputs = [inputs[0]-1]
            case "wire":
                outputs = [inputs[0]]
            case "split":
                outputs = [inputs[0],inputs[0]]
            case "3split":
                outputs = [inputs[0],inputs[0],inputs[0]]
            case "27split":
                outputs = [inputs[0]] * 27
            case "sub":
                outputs = [min(max(inputs[0]-inputs[1],-1),1)]
            case "mul":
                outputs = [inputs[0]*inputs[1]]
            case "and":
                if inputs[0] == inputs[1]:
                    outputs = [inputs[0]]
                else:
                    outputs = [0]
            case "ripple":
                if inputs[0] == 0:
                    outputs = [inputs[1]]
                else:
                    outputs = [inputs[0]]
            case "3pos":
                outputs = [0,0,0]
                for item in range(3):
                    if inputs[item] == 1:
                        outputs[item] = 1
                    else:
                        outputs[item] = 0
            case "half_adder":
                if inputs[0]==inputs[1]:
                    outputs = [inputs[0],-1*inputs[0]]
                else:
                    outputs = [0,inputs[0]+inputs[1]]
            case "adder":
                total = inputs[0]+inputs[1]+inputs[2]
                outputs = [int(total/2),total-3*int(total/2)]
            case "sr_latch":
                outputs = self.memory
                for input in range(3):
                    if inputs[input] == 1:
                        outputs[0] = 1-input
                        break
                self.memory = outputs
            case "d_latch":
                outputs = self.memory
                if inputs[1] == 1:
                    outputs[0] = inputs[0]
            case "3reg":
                if inputs[3] == 1:
                    self.memory = inputs[:3]
                outputs = self.memory
            case "3mem":
                location = 9*inputs[3]+3*inputs[4]+inputs[5]
                if inputs[6] == 1:
                    self.memory[location] = inputs[:3]
                if inputs[6] == -1:
                    if location in self.memory:
                        outputs = self.memory[location]
                    else:
                        outputs = [0,0,0]
                else:
                    return
            case "control":
                location = 729*inputs[6]+243*inputs[7]+81*inputs[8]+9*inputs[9]+3*inputs[10]+inputs[11]
                if inputs[12] == 1:
                    self.memory[location] = inputs[:6]
                if inputs[12] == -1:
                    if location in self.memory:
                        outputs = self.memory[location]
                    else:
                        outputs = [0,0,0,0,0,0]
                else:
                    return
            case "relay":
                if inputs[3] == 1:
                    outputs = inputs[:3]
                elif inputs[3] == -1:
                    outputs = [-i for i in inputs[:3]]
                else:
                    outputs = [0,0,0]
            case "buffer":
                if inputs[3] == 1:
                    outputs = inputs[:3]
                else:
                    return
            case "demux":
                outputs = [0] * 27
                outputs[9*inputs[1]+3*inputs[2]+inputs[3]+13] = inputs[0]
            case "mux":
                outputs = [inputs[inputs[27]*9+inputs[28]*3+inputs[29]+13]]
                

            case "out":
                outputs = []
                #print(outputs)
            case "dummy":
                outputs = []
            case "test":
                outputs = [None] * gate_style[1]
                for i in range(gate_style[1]):
                    outputs[i] = inputs[i]
            case other:
                if self.gate_type in custom_gates:
                    inputstring = ''
                    for input in inputs:
                        match input:
                            case 1:
                                inputstring += '+'
                            case -1:
                                inputstring += '-'
                            case 0:
                                inputstring += '0'
                    outputs = custom_gates[self.gate_type][inputstring]

                else:
                    print(f"gate {self.gate_type} not found")
                    #TODO: finding gate from file
                    print("finding gates from file not implemented")
                    exit()

        for i in range(gate_styles[self.gate_type][2]):
            destination = self.destinations[i]
            if destination == None:
                continue

            value = outputs[i]

            if circuit[destination[0]].values[destination[1]] == value:
                continue
            else:
                circuit[destination[0]].values[destination[1]] = value
            if destination[0] not in tasklist:
                tasklist.append(destination[0])
    
    def update_wires(self):
        gate_style = gate_styles[self.gate_type]
        input_height = gate_style[0]/gate_style[1]
        if not self.wires:
            for i in range(gate_style[1]):
                self.wires.append([None,None])
        for i, source in enumerate(self.sources):
            end = (self.rect[0]+1.5*PORT_RADIUS,self.rect[1]+(i+0.5)*input_height)
            if source == None:
                self.wires[i] = [end,end]
                continue
            source_component = circuit[source[0]]
            source_style = gate_styles[source_component.gate_type]
            source_height = source_style[0]/source_style[2]
            self.wires[i][0] = (source_component.rect[0]+GATE_WIDTH-1.5*PORT_RADIUS,source_component.rect[1]+(source[1]+0.5)*source_height)
            self.wires[i][-1] = end

    def inports_collision(self, mouse_pos):
        gate_style = gate_styles[self.gate_type]
        input_height = gate_style[0]/gate_style[1]
        for port in range(len(self.sources)):
            if abs(mouse_pos[1]-self.rect[1]-(port+0.5)*input_height)<PORT_RADIUS+2:
                return port

    def outports_collision(self, mouse_pos):
        if self.gate_type == "out":
            return
        gate_style = gate_styles[self.gate_type]
        output_height = gate_style[0]/gate_style[2]
        for port in range(len(self.destinations)):
            if abs(mouse_pos[1]-self.rect[1]-(port+0.5)*output_height)<PORT_RADIUS+2:
                return port
            
    def modify_inport(self, port, new_source):
        global active_port_in
        if self.sources[port]:
            circuit[self.sources[port][0]].destinations[self.sources[port][1]] = None
        circuit[active_gate].sources[active_port_in] = None

        self.sources[port] = new_source
        circuit[new_source[0]].destinations[new_source[1]] = (self.id,port)

        self.update_wires()
        circuit[active_gate].update_wires()
        circuit[new_source[0]].update_wires()

        tasklist.append(active_gate)
        tasklist.append(new_source[0])

        active_port_in = None

        process(circuit)

    def modify_outport(self, port, new_destination):
        global active_port_out
        if self.destinations[port]:
            circuit[self.destinations[port][0]].sources[self.destinations[port][1]] = None
            circuit[self.destinations[port][0]].update_wires()
        circuit[active_gate].destinations[active_port_out] = None

        self.destinations[port] = new_destination
        circuit[new_destination[0]].sources[new_destination[1]] = (self.id,port)

        circuit[new_destination[0]].update_wires()
        circuit[active_gate].update_wires()

        tasklist.append(self.id)
        tasklist.append(new_destination[0])
        tasklist.append(active_gate)

        active_port_out = None

        process(circuit)
    def render_gate(self):
        if self.id == -2:
            return
        gate_style = gate_styles[self.gate_type]
        match self.gate_type:
            # case "input":
            #     return
            # case "out":
            #     return
            case other:
                font = pygame.font.Font(None, 32)
                pygame.draw.rect(display,gate_style[3],self.rect,border_radius=5)
                text = font.render(self.gate_type, True, (10, 10, 10))
                textpos = text.get_rect(centerx=(self.rect.width/2)+self.rect[0], centery=(self.rect.height/2)+self.rect[1])
                display.blit(text, textpos)
                for outport in range(gate_style[2]):
                    output_height = gate_style[0]/gate_style[2]
                    origin = (self.rect[0]+GATE_WIDTH-1.5*PORT_RADIUS,self.rect[1]+(outport+0.5)*output_height)
                    pygame.draw.rect(display,BACKGROUND_COLOUR,pygame.Rect(origin[0]-PORT_RADIUS,origin[1]-PORT_RADIUS,PORT_RADIUS*2,PORT_RADIUS*2),border_radius=3)
                




    def render_wires(self):
        gate_style = gate_styles[self.gate_type]
        for i in range(gate_style[1]):
            try:
                colour = colours[self.values[i]]
            except:
                colour = BACKGROUND_COLOUR
            origin, *_, end = self.wires[i]
            if not end:
                continue

            # pygame.draw.circle(display, colour, end, PORT_RADIUS)
            pygame.draw.rect(display,colour,pygame.Rect(end[0]-PORT_RADIUS,end[1]-PORT_RADIUS,PORT_RADIUS*2,PORT_RADIUS*2),border_radius=3)

            pygame.draw.aalines(display, colour, False, self.wires[i])
            # pygame.draw.lines(display, colour, False, self.wires[i],5)
            # pygame.draw.circle(display, colour, start, PORT_RADIUS)
            pygame.draw.rect(display,colour,pygame.Rect(origin[0]-PORT_RADIUS,origin[1]-PORT_RADIUS,PORT_RADIUS*2,PORT_RADIUS*2),border_radius=3)
