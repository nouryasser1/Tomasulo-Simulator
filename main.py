import re

memory = []
starting_adress = 0
instructions = []
def start():
    print("--------------------Tomasulo's Algorithm ------------------")
    #Memory initialization
    for i in range(6400):
        memory.append(0)
    starting_adress = (input("Please enter your starting adress: "))
    while(not(starting_adress.isdigit())):
        starting_adress = (input("Please enter your starting adress as an integer: "))
    new_addr = 'Y'
    while new_addr != 'N' and new_addr != 'n':
        address = (input("Please enter an adress you want to use: "))
        data_in = (input("Please enter the data in 16 bits: "))

        if ((not address.isdigit()) or (not data_in.isdigit())):
            print("Invalid address, not allowed")
        else:
            address = int(address)
            data_in = int(data_in)
            if address > 10 or data_in > 65536:
                print("Invalid range")
            else:
                memory[address] = data_in

        new_addr = input("Do you want to add other adresses? (Y/N)")
        print(new_addr)

    #Instructions intialization and validation

    new_inst = 'y'
    inst_structured=[] #For applying the different structures of instructions
    while new_inst != 'N' and new_inst != 'n':
        inst = (input("Please enter an instruction you want to add to your program"))
        inst = inst.lower().replace(" ", "")
        print(inst)
        if (validation(inst) == False):
            print("Invalid instruction")
        else:
            if(inst[0:4] == 'load'):
                inst_structured=[inst[0:4],inst[4:6], inst[7:inst.index('(')], inst[inst.index('(')+1:inst.index(')')]]
            elif(inst[0:5] == 'store'):
                inst_structured = [inst[0:5], inst[5:7], inst[8:inst.index('(')],inst[inst.index('(') + 1:inst.index(')')]]
            elif(inst[0:3] == 'beq' or inst[0:3] == 'add' or inst[0:3] == 'mul'):
                inst_structured = [inst[0:3], inst[3:5], inst[6:8], inst[9:]]
            elif(inst[0:4] == 'addi' or inst[0:3] == 'nand'):
                inst_structured = [inst[0:4], inst[4:6], inst[7:9], inst[10:]]
            elif(inst[0:4] == 'call'):
                inst_structured = [inst[0:4], inst[4:], None, None]
            elif(inst[0:3] == 'ret'):
                inst_structured = [inst[0:3], None, None, None]
            instructions.append(inst_structured)
        new_inst = input("Do you want to add other instruction? (Y/N)")
    print(instructions)
def validation(inst): #function which uses regex to validates the format of the instruction
    if inst[0:4] == 'load' or inst[0:5] == 'store':
        if(inst[7:9] == '16'):
            return False
        else:
            inst_pattern = re.compile(r'(load|store)r[0-7],(-?(?:-?1[0-6]|-?[0-9]|1[0-6])\(r[0-7]\)$)')
            matching = inst_pattern.match(inst)
    elif inst[0:3] == 'beq':
        if (inst[9:11] == '16'):
            return False
        else:
            inst_pattern = re.compile(r'(beq)r[0-7],r[0-7],(-?(?:1[0-6]|[0-9]))$')
            matching = inst_pattern.match(inst)
    elif inst[0:4] == 'addi':
        if (inst[10:12] == '16'):
            return False
        else:
            inst_pattern = re.compile(r'(addi)r[0-7],r[0-7],-?(?:1[0-6]|[0-9])$')
            matching = inst_pattern.match(inst)
    elif inst[0:4] == 'call':
        if (inst[4:6] == '16'):
            return False
        else:
            inst_pattern = re.compile(r'(call)(-?(?:1[0-6]|[0-9]))$')
            matching = inst_pattern.match(inst)
    elif inst[0:3] == 'ret':
        inst_pattern = re.compile(r'(ret)$')
        matching = inst_pattern.match(inst)
    elif inst[0:3] == 'add' or inst[0:3] == 'mul' or inst[0:4] == 'nand':
        inst_pattern = re.compile(r'(add|mul|nand)r[0-7],r[0-7],r[0-7]$')
        matching = inst_pattern.match(inst)
    else:
        matching = False
    print(matching)
    return bool(matching)
start()