import pickle
import sys

import pygame

from data import *

clock = pygame.time.Clock()
from pygame.locals import *

pygame.init()
pygame.display.set_caption("Ternary Simulator")
icon = pygame.Surface((10, 10))
icon.fill((255, 255, 255))
pygame.display.set_icon(icon)


if sys.platform == "win32":
    # On Windows, the monitor scaling can be set to something besides normal 100%.
    # PyScreeze and Pillow needs to account for this to make accurate screenshots.
    import ctypes

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except AttributeError:
        pass  # Windows XP doesn't support monitor scaling, so just do nothing.

if len(sys.argv) < 2:
    blueprint = "cpu"  # <<< Replace this default to liking
else:
    blueprint = sys.argv[1]


# WINDOW_SIZE = (800,400)
WINDOW_SIZE = (1600, 900)
BACKGROUND_COLOUR = (40, 36, 56)
GATE_WIDTH = 130
PORT_RADIUS = 7
screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
display = pygame.Surface((1600, 900))

update_required = True
active_gate = None
active_port_in = None
active_port_out = None
tasklist = []
next_component = 0
testing = False
selected_gate = None


try:
    with open(f"./circuits/{blueprint}.pkl", "rb") as f:
        input_circuit = pickle.load(f)
    print(f"blueprint file [{blueprint}] loaded")
except:
    print(
        f"no blueprint file (./circuits/{blueprint}.pkl) detected, loading standard MUL circuit"
    )
    input_circuit = {
        0: [
            "input",
            [1, 1, 1, 0, 0, 0, -1, -1, -1],
            [None, None, None, None, None, None, None, None, None],
            [50, 300],
        ],
        1: ["split", None, [(4, 0), (3, 0)], [200, 300]],
        2: ["split", None, [(4, 1), (3, 1)], [200, 450]],
        3: ["min", None, [(6, 1)], [375, 450]],
        4: ["max", None, [(5, 0)], [375, 300]],
        5: ["neg", None, [(6, 0)], [530, 325]],
        6: ["max", None, [(-1, 0)], [700, 375]],
        -1: ["out", None, [], [875, 400]],
        -2: ["dummy", [2], [(-2, 0)], [-500, -500]],
    }

# input_circuit[0][1] = [1,1,1,0,0,0,-1,-1,-1]
# input_circuit[0][2] = [None,None,None,None,None,None,None,None,None]

# TODO: import custom gates
# custom_gates = {
#     "pos": {'0':[1],'+':[1],'-':[2]}
# }

input_length = len(input_circuit[0][2])
gate_styles["input"] = [25 * input_length, input_length, input_length, (123, 74, 195)]


class Component:
    def __init__(self, id, argument):
        self.gate_type, values, destinations, position, *_ = argument
        self.id = id
        self.rect = pygame.Rect(position, (GATE_WIDTH, gate_styles[self.gate_type][0]))
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
                self.memory = [0, 0, 0]
            elif self.gate_type in ["3mem", "control"]:
                self.memory = {}
            else:
                self.memory = None

    def update_outports(self):  # updates destination gates' sources
        for num, destination in enumerate(self.destinations):
            if destination:
                circuit[destination[0]].sources[destination[1]] = (self.id, num)

    def update_inports(self):  # updates destination gates' sources
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
                outputs = [inputs[0] * -1]
            case "max":
                outputs = [max(inputs[0], inputs[1])]
            case "min":
                outputs = [min(inputs[0], inputs[1])]
            case "inc":
                if inputs[0] == 1:
                    outputs = [-1]
                else:
                    outputs = [inputs[0] + 1]
            case "dec":
                if inputs[0] == -1:
                    outputs = [1]
                else:
                    outputs = [inputs[0] - 1]
            case "wire":
                outputs = [inputs[0]]
            case "split":
                outputs = [inputs[0], inputs[0]]
            case "3split":
                outputs = [inputs[0], inputs[0], inputs[0]]
            case "27split":
                outputs = [inputs[0]] * 27
            case "sub":
                outputs = [min(max(inputs[0] - inputs[1], -1), 1)]
            case "mul":
                outputs = [inputs[0] * inputs[1]]
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
                outputs = [0, 0, 0]
                for item in range(3):
                    if inputs[item] == 1:
                        outputs[item] = 1
                    else:
                        outputs[item] = 0
            case "half_adder":
                if inputs[0] == inputs[1]:
                    outputs = [inputs[0], -1 * inputs[0]]
                else:
                    outputs = [0, inputs[0] + inputs[1]]
            case "adder":
                total = inputs[0] + inputs[1] + inputs[2]
                outputs = [int(total / 2), total - 3 * int(total / 2)]
            case "sr_latch":
                outputs = self.memory
                for input in range(3):
                    if inputs[input] == 1:
                        outputs[0] = 1 - input
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
                location = 9 * inputs[3] + 3 * inputs[4] + inputs[5]
                if inputs[6] == 1:
                    self.memory[location] = inputs[:3]
                if inputs[6] == -1:
                    if location in self.memory:
                        outputs = self.memory[location]
                    else:
                        outputs = [0, 0, 0]
                else:
                    return
            case "control":
                location = (
                    729 * inputs[6]
                    + 243 * inputs[7]
                    + 81 * inputs[8]
                    + 9 * inputs[9]
                    + 3 * inputs[10]
                    + inputs[11]
                )
                if inputs[12] == 1:
                    self.memory[location] = inputs[:6]
                if inputs[12] == -1:
                    if location in self.memory:
                        outputs = self.memory[location]
                    else:
                        outputs = [0, 0, 0, 0, 0, 0]
                else:
                    return
            case "relay":
                if inputs[3] == 1:
                    outputs = inputs[:3]
                elif inputs[3] == -1:
                    outputs = [-i for i in inputs[:3]]
                else:
                    outputs = [0, 0, 0]
            case "buffer":
                if inputs[3] == 1:
                    outputs = inputs[:3]
                else:
                    return
            case "demux":
                outputs = [0] * 27
                outputs[9 * inputs[1] + 3 * inputs[2] + inputs[3] + 13] = inputs[0]
            case "mux":
                outputs = [inputs[inputs[27] * 9 + inputs[28] * 3 + inputs[29] + 13]]

            case "out":
                outputs = []
                # print(outputs)
            case "dummy":
                outputs = []
            case "test":
                outputs = [None] * gate_style[1]
                for i in range(gate_style[1]):
                    outputs[i] = inputs[i]
            case other:
                if self.gate_type in custom_gates:
                    inputstring = ""
                    for input in inputs:
                        match input:
                            case 1:
                                inputstring += "+"
                            case -1:
                                inputstring += "-"
                            case 0:
                                inputstring += "0"
                    outputs = custom_gates[self.gate_type][inputstring]

                else:
                    print(f"gate {self.gate_type} not found")
                    # TODO: finding gate from file
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
        input_height = gate_style[0] / gate_style[1]
        if not self.wires:
            for i in range(gate_style[1]):
                self.wires.append([None, None])
        for i, source in enumerate(self.sources):
            end = (
                self.rect[0] + 1.5 * PORT_RADIUS,
                self.rect[1] + (i + 0.5) * input_height,
            )
            if source == None:
                self.wires[i] = [end, end]
                continue
            source_component = circuit[source[0]]
            source_style = gate_styles[source_component.gate_type]
            source_height = source_style[0] / source_style[2]
            self.wires[i][0] = (
                source_component.rect[0] + GATE_WIDTH - 1.5 * PORT_RADIUS,
                source_component.rect[1] + (source[1] + 0.5) * source_height,
            )
            self.wires[i][-1] = end

    def inports_collision(self, mouse_pos):
        gate_style = gate_styles[self.gate_type]
        input_height = gate_style[0] / gate_style[1]
        for port in range(len(self.sources)):
            if (
                abs(mouse_pos[1] - self.rect[1] - (port + 0.5) * input_height)
                < PORT_RADIUS + 2
            ):
                return port

    def outports_collision(self, mouse_pos):
        if self.gate_type == "out":
            return
        gate_style = gate_styles[self.gate_type]
        output_height = gate_style[0] / gate_style[2]
        for port in range(len(self.destinations)):
            if (
                abs(mouse_pos[1] - self.rect[1] - (port + 0.5) * output_height)
                < PORT_RADIUS + 2
            ):
                return port

    def modify_inport(self, port, new_source):
        global active_port_in
        if self.sources[port]:
            circuit[self.sources[port][0]].destinations[self.sources[port][1]] = None
        circuit[active_gate].sources[active_port_in] = None

        self.sources[port] = new_source
        circuit[new_source[0]].destinations[new_source[1]] = (self.id, port)

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
            circuit[self.destinations[port][0]].sources[
                self.destinations[port][1]
            ] = None
            circuit[self.destinations[port][0]].update_wires()
        circuit[active_gate].destinations[active_port_out] = None

        self.destinations[port] = new_destination
        circuit[new_destination[0]].sources[new_destination[1]] = (self.id, port)

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
                pygame.draw.rect(display, gate_style[3], self.rect, border_radius=5)
                text = font.render(self.gate_type, True, (10, 10, 10))
                textpos = text.get_rect(
                    centerx=(self.rect.width / 2) + self.rect[0],
                    centery=(self.rect.height / 2) + self.rect[1],
                )
                display.blit(text, textpos)
                for outport in range(gate_style[2]):
                    output_height = gate_style[0] / gate_style[2]
                    origin = (
                        self.rect[0] + GATE_WIDTH - 1.5 * PORT_RADIUS,
                        self.rect[1] + (outport + 0.5) * output_height,
                    )
                    pygame.draw.rect(
                        display,
                        BACKGROUND_COLOUR,
                        pygame.Rect(
                            origin[0] - PORT_RADIUS,
                            origin[1] - PORT_RADIUS,
                            PORT_RADIUS * 2,
                            PORT_RADIUS * 2,
                        ),
                        border_radius=3,
                    )

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
            pygame.draw.rect(
                display,
                colour,
                pygame.Rect(
                    end[0] - PORT_RADIUS,
                    end[1] - PORT_RADIUS,
                    PORT_RADIUS * 2,
                    PORT_RADIUS * 2,
                ),
                border_radius=3,
            )

            pygame.draw.aalines(display, colour, False, self.wires[i])
            # pygame.draw.lines(display, colour, False, self.wires[i],5)
            # pygame.draw.circle(display, colour, start, PORT_RADIUS)
            pygame.draw.rect(
                display,
                colour,
                pygame.Rect(
                    origin[0] - PORT_RADIUS,
                    origin[1] - PORT_RADIUS,
                    PORT_RADIUS * 2,
                    PORT_RADIUS * 2,
                ),
                border_radius=3,
            )


def process(circuit):
    global tasklist
    global recentlist
    if not tasklist:
        recentlist = [-2, -2, -2, -2, -2]
        circuit[0].update_gate()

    counter = 0
    while tasklist:
        if testing:
            print(tasklist)
        next_task = tasklist[0]
        recentlist.append(next_task)
        tasklist.pop(0)
        circuit[next_task].update_gate()

        counter += 1
        if counter > 100:
            print("max cycles exceeded")
            break


def save_circuit():
    file_name = input("please input file name: ")

    output_circuit = {}

    # TODO: simplify circuit to lower numbers
    # counter = 1
    # for item in circuit:
    #     if item>0:
    #         changeid(item, counter)
    #         counter += 1

    for item in circuit:
        component = circuit[item]
        if component.memory:
            output_circuit[item] = [
                component.gate_type,
                component.values,
                component.destinations,
                [component.rect[0], component.rect[1]],
                component.memory,
            ]
        else:
            output_circuit[item] = [
                component.gate_type,
                component.values,
                component.destinations,
                [component.rect[0], component.rect[1]],
            ]

    with open(f"./circuits/{file_name}.pkl", "wb") as f:
        pickle.dump(output_circuit, f)


circuit = {}
for item in input_circuit:
    circuit[item] = Component(item, input_circuit[item])
for component in circuit:
    circuit[component].update_outports()
for component in circuit:
    circuit[component].update_wires()
    next_component = max(component, next_component)


next_component += 1


process(circuit)


while True:
    # if testing:
    #     print()

    # event handler
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_RIGHT:
                print("Available gates:")
                for gate in gate_styles:
                    print(gate)
                # TODO: allow custom_gates
                # for gate in custom_gates:
                #     print(gate)

                gate_type = input("new gate type >")
                if gate_type not in gate_styles:
                    print(f"{gate_type} gate not recognised")
                    continue
                gate_style = gate_styles[gate_type]
                circuit[next_component] = Component(
                    next_component, [gate_type, None, None, (0, 0)]
                )
                circuit[next_component].update_inports()
                circuit[next_component].update_outports()
                circuit[next_component].update_wires()
                next_component += 1
            elif event.key == K_LEFT:
                testing = not testing
            elif event.key == K_DOWN:
                save_circuit()
            elif event.key == K_DELETE:
                if selected_gate != None:
                    for source in circuit[selected_gate].sources:
                        if source:
                            circuit[source[0]].destinations[source[1]] = None
                    for destination in circuit[selected_gate].destinations:
                        if destination:
                            circuit[destination[0]].sources[destination[1]] = None
                            circuit[destination[0]].update_wires()
                    circuit.pop(selected_gate)
                    selected_gate = None
            elif event.key == K_r:
                # for item in circuit:
                #     tasklist.append(item)
                process(circuit)
        if event.type == MOUSEBUTTONUP:
            if active_port_in != None:
                for num in circuit:
                    component = circuit[num]
                    if (
                        component.rect.collidepoint(event.pos)
                        and event.pos[0] < component.rect[0] + PORT_RADIUS * 2
                    ):
                        port = component.inports_collision(event.pos)
                        if port != None:
                            component.modify_inport(
                                port, circuit[active_gate].sources[active_port_in]
                            )
                            port = None
                            break
            elif active_port_out != None:
                for num in circuit:
                    component = circuit[num]
                    if (
                        component.rect.collidepoint(event.pos)
                        and event.pos[0] > component.rect[0] - PORT_RADIUS * 2
                    ):
                        port = component.outports_collision(event.pos)
                        if port != None:
                            component.modify_outport(
                                port, circuit[active_gate].destinations[active_port_out]
                            )
                            port = None
                            break

            if active_port_in != None:
                if active_gate == -2:
                    circuit[active_gate].sources[0] = (-2, 0)
                circuit[active_gate].update_wires()
            elif active_port_out != None:
                to_update = circuit[active_gate].destinations[active_port_out]
                if to_update:
                    circuit[to_update[0]].update_wires()

            active_gate = None
            active_port_in = None
            active_port_out = None

        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:

                for num in circuit:
                    if active_gate:
                        break
                    component = circuit[num]
                    if component.rect.collidepoint(event.pos):
                        active_gate = num
                        selected_gate = num

                        if event.pos[0] < component.rect[0] + PORT_RADIUS * 2.5:
                            active_port_in = component.inports_collision(event.pos)
                            if (
                                active_port_in != None
                                and circuit[active_gate].sources[active_port_in] == None
                            ):
                                circuit[-2].destinations[0] = (
                                    active_gate,
                                    active_port_in,
                                )
                                active_gate = -2
                                active_port_out = 0
                                active_port_in = None

                        elif (
                            event.pos[0]
                            > component.rect[0] + GATE_WIDTH - PORT_RADIUS * 2.5
                        ):
                            active_port_out = component.outports_collision(event.pos)
                            if (
                                active_port_out != None
                                and circuit[active_gate].destinations[active_port_out]
                                == None
                            ):
                                circuit[-2].sources[0] = (active_gate, active_port_out)
                                circuit[-2].update_wires()
                                circuit[-2].wires[0][-1] = event.pos
                                active_gate = -2
                                active_port_out = None
                                active_port_in = 0

        if event.type == MOUSEMOTION:
            if active_port_in != None:
                circuit[active_gate].wires[active_port_in][-1] = event.pos
            elif active_port_out != None:
                destination = circuit[active_gate].destinations[active_port_out]
                if destination:
                    circuit[destination[0]].wires[destination[1]][0] = event.pos
            elif active_gate != None:
                if active_gate == 0:
                    continue
                circuit[active_gate].rect.move_ip(event.rel)
                circuit[active_gate].update_wires()
                for destination_gate in circuit[active_gate].destinations:
                    if destination_gate == None:
                        continue
                    circuit[destination_gate[0]].update_wires()

    # render components on display
    for component in circuit:
        circuit[component].render_gate()
    for component in circuit:
        circuit[component].render_wires()

    if update_required:
        screen.blit(pygame.transform.scale(display, WINDOW_SIZE), (0, 0))
        # screen.blit(display,(0,0))
        pygame.display.update()
        display.fill(BACKGROUND_COLOUR)
    clock.tick(60)
