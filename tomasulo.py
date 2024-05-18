import tabulate
import re

#Lists Used
memory = []
instructions = []

current_reservation_stations = [] #to refer to the RS we are updating 3
issued = [] #instructions need to be issued 3
execution_time = [] # the execution time with in sync index as issued
waiting_for_write = [] #instructions awaiting writing
write_flag = [] #flag that instruction is available for writing

#Variables used all over the code
starting_address = 0 #taken from user and need to be used to calculate the PCs
write_val = 0 #represents the value written to replace in the reservation station
issue_flag = False
issue_rs = ""
addV = [0,0,0,0]
nandV = [0,0]
mulV = 0
#Branch flags and variables to handle the branch
branch_taken_flag = False #indicates that the branch result should be taken or not
branch_issue_flag = False #indicates that a branch instruction is being issued
branch_write_flag = False #indicates that the branch instruction is written
branch_stall_exec_flag = False #this is a flag to indicate that we will not execute the issued instructions after the branch unless the writing flag indicates true and tells us if branch was not taken
branch_instruction_position = 100 #to identify the position of our branch within the list to manipulate the flushing 

#Cal/Ret flags 
call_ret_issue_flag = False #indicates that a cal ret instruction is being issued
call_ret_write_flag = False #indicates that a cal ret instruction is being written
cal_ret_stall_issue_flag = False #indicates that we will not issue new instructions until we jump

#Variables for Calculations Required
number_of_branch_taken = 0 
total_branches = 0 
total_clock_cycles = 0

#Reservation Station Table
LOAD_1 = {"Name" : "LOAD1", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
LOAD_2 = {"Name" : "LOAD2", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
STORE = {"Name" : "STORE", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
BEQ = {"Name" : "BEQ", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
CALL_OR_RET = {"Name" : "CALL/RET", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
ADD_OR_ADDI_1 = {"Name" : "ADD/ADDI 1", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
ADD_OR_ADDI_2 = {"Name" : "ADD/ADDI 2", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
ADD_OR_ADDI_3 = {"Name" : "ADD/ADDI 3", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
ADD_OR_ADDI_4 = {"Name" : "ADD/ADDI 4", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
NAND_1 = {"Name" : "NAND1", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
NAND_2 = {"Name" : "NAND2", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}
MUL = {"Name" : "MUL", "Busy" : 'N', "Op" : None, "Vj" : None, "Vk" : None, "Qj" : None, "Qk" : None, "A" : None, "Imm" : None}

RS = [LOAD_1, LOAD_2, STORE, BEQ, CALL_OR_RET, ADD_OR_ADDI_1, ADD_OR_ADDI_2, ADD_OR_ADDI_3, ADD_OR_ADDI_4, NAND_1, NAND_2, MUL]

def print_RS_table():
    headings = list(RS[0].keys())
    headings = headings[:-1]
    table = [list(row.values()) for row in RS]
    table = [row[:-1] for row in table]
    print(tabulate.tabulate(table, headings, tablefmt="double_outline"))
    

#Tracing Table
TracingDictionary = {"Instructions" : None, "Issue" : None, "Execution Start" : None, "Execution End" : None, "Write" : None}

TraceTable = [] #gets appended by issued instructions

def print_trace_table():
    headings = TraceTable[0].keys()
    table = [row.values() for row in TraceTable]
    print(tabulate.tabulate(table, headings, tablefmt="double_outline"))

#Register Status
RegStatus = {"r0" : None, "r1" : None, "r2" : None, "r3" : None, "r4" : None, "r5" : None, "r6" : None, "r7" : None}

def print_register_status():
    headings = RegStatus.keys()
    row =  [RegStatus.values()]
    print(tabulate.tabulate(row, headings, tablefmt="double_outline"))

#Register Values
RegFile = {"r0" : 0, "r1" : 0, "r2" : 0, "r3" : 0, "r4" : 0, "r5" : 0, "r6" : 0, "r7" : 0}

def print_reg_file():
    headings = RegFile.keys()
    row =  [RegFile.values()]
    print(tabulate.tabulate(row, headings, tablefmt="double_outline"))

def issue (instruction, last_written, PC): # the current instruction against the last FU that was written
    global issue_flag
    global issue_rs
    global call_ret_issue_flag
    global branch_issue_flag
    global branch_instruction_position
    print(instruction, "issuing")
    if(instruction[0] == "load"):
        if(last_written != "LOAD1" or last_written != "LOAD2"):
            if(LOAD_1["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[0]
               
            elif(LOAD_2["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[1]
                
            else:
                issue_flag = False
                issue_rs = None
            
            if(issue_flag):
                issue_rs["Busy"] = "Y"
                issue_rs["Op"] = instruction[0]
                issue_rs["Vj"] = RegFile[instruction[3]]
                print("vj",RegFile[instruction[3]],instruction[3] )
                issue_rs["Vk"] = None
                issue_rs["Qj"] = None
                issue_rs["Qk"] = None
                issue_rs["A"] = int(instruction[2])
                issue_rs["Imm"] = None

                if (RegStatus[instruction[3]] != None):
                    issue_rs["Vj"] = None
                    issue_rs["Qj"] = RegStatus[instruction[3]]
                if(instruction[1] != "r0"):
                    RegStatus[instruction[1]] = issue_rs["Name"]
                current_reservation_stations.append(issue_rs)
                issued.append(instruction)
                execution_time.append(0)
                write_flag.append(False)

    elif(instruction[0] == "store"):
        if(last_written != "STORE"): 
            if(STORE["Busy"] == "N"): 
                issue_flag = True
                issue_rs = RS[2]
                issue_rs["Busy"] = "Y"
                issue_rs["Op"] = instruction[0]
                issue_rs["Vj"] = RegFile[instruction[1]]
                issue_rs["Vk"] = RegFile[instruction[3]]
                issue_rs["Qj"] = None
                issue_rs["Qk"] = None
                issue_rs["A"] = int(instruction[2])
                issue_rs["Imm"] = None

                if (instruction[1] != "r0" and RegStatus[instruction[1]] != None):
                    issue_rs["Vj"] = None
                    issue_rs["Qj"] = RegStatus[instruction[1]]
                
                if (instruction[3] != "r0" and RegStatus[instruction[3]] != None):
                    issue_rs["Vk"] = None
                    issue_rs["Qk"] = RegStatus[instruction[3]]

                RegStatus[instruction[3]] = issue_rs["Name"]
                
                current_reservation_stations.append(issue_rs)
                issued.append(instruction)
                execution_time.append(0)
                write_flag.append(False)
                
            else:
                issue_flag = False
                issue_rs = None

    elif(instruction[0] == "beq"):
        if(last_written != "BEQ"):
            if(BEQ["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[3]
                issue_rs["Busy"] = "Y"
                issue_rs["Op"] = instruction[0]
                issue_rs["Vj"] = RegFile[instruction[1]]
                issue_rs["Vk"] = RegFile[instruction[2]]
                issue_rs["Qj"] = None
                issue_rs["Qk"] = None
                issue_rs["A"] = int(instruction[3])
                issue_rs["Imm"] = PC #instruction branch position

                if(instruction[1] != "r0" and RegStatus[instruction[1]] != None):
                    issue_rs["Vj"] = None
                    issue_rs["Qj"] = RegStatus[instruction[1]]
                if(instruction[2] != "r0" and RegStatus[instruction[2]] != None):
                    issue_rs["Vk"] = None
                    issue_rs["Qk"] = RegStatus[instruction[2]]
                current_reservation_stations.append(issue_rs)
                issued.append(instruction)
                execution_time.append(0)
                write_flag.append(False)
                branch_issue_flag = True
                branch_instruction_position = (len(issued)- 1)

            else:
                issue_flag = False
                issue_rs = None

    elif(instruction[0] == "call" or instruction[0] == "ret"):
        if(last_written != "CALL_OR_RET"):
            if(CALL_OR_RET["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[4]
            else:
                issue_flag = False
                issue_rs = None
            if(issue_flag):
                issue_rs["Busy"] = "Y"
                issue_rs["Op"] = instruction[0] 
                issue_rs["Vk"] = None
                issue_rs["Qj"] = None
                issue_rs["Qk"] = None
                if(instruction[0] == "call"):
                    issue_rs["Vj"] = None
                    issue_rs["A"] = int(instruction[1]) 
                    issue_rs["Imm"] = PC
                    RegStatus["r1"] = issue_rs["Name"]
                else: #ret
                    issue_rs["Vj"] = "r1"
                    issue_rs["A"] = int(RegFile["r1"])

                    if(RegStatus["r1"] != None):
                        issue_rs["Vj"] = None
                        issue_rs["Qj"] = RegStatus["r1"]

                current_reservation_stations.append(issue_rs)
                issued.append(instruction)
                execution_time.append(0)
                write_flag.append(False)
                call_ret_issue_flag = True                

    elif(instruction[0] == "add" or instruction[0] == "addi"):
        if(last_written != "ADD_OR_ADDI_1" or last_written != "ADD_OR_ADDI_2" or last_written != "ADD_OR_ADDI_3" or last_written != "ADD_OR_ADDI_4"):
            if(ADD_OR_ADDI_1["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[5]
            elif(ADD_OR_ADDI_2["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[6]
            elif(ADD_OR_ADDI_3["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[7]
            elif(ADD_OR_ADDI_4["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[8]
            else:
                issue_flag = False
                issue_rs = None
            if(issue_flag): 
                issue_rs["Busy"] = "Y"
                issue_rs["Op"] = instruction[0]
                issue_rs["Vj"] = RegFile[instruction[2]]
                issue_rs["Qj"] = None
                issue_rs["Qk"] = None
                issue_rs["A"] = None
                if(instruction[0] == "add"):
                    issue_rs["Vk"] = RegFile[instruction[3]]
                    issue_rs["Imm"] = None
                    if(instruction[2] != "r0" and RegStatus[instruction[2]] != None):
                        issue_rs["Vj"] = None
                        issue_rs["Qj"] = RegStatus[instruction[2]]
                    if(instruction[3] != "r0" and RegStatus[instruction[3]] != None):
                        issue_rs["Vk"] = None
                        issue_rs["Qk"] = RegStatus[instruction[3]]
                    if(instruction[1] != "r0"):
                        RegStatus[instruction[1]] = issue_rs["Name"]
                else:#addi
                    issue_rs["Vk"] = None
                    issue_rs["Imm"] = int(instruction[3])
                    if(instruction[2] != "r0" and RegStatus[instruction[2]] != None):
                        issue_rs["Vj"] = None
                        issue_rs["Qj"] = RegStatus[instruction[2]]
                    if(instruction[1] != "r0"):
                        RegStatus[instruction[1]] = issue_rs["Name"]
                current_reservation_stations.append(issue_rs)
                issued.append(instruction)
                execution_time.append(0)
                write_flag.append(False)

    elif(instruction[0]  == "nand"):
        if(last_written != "NAND1" or last_written != "NAND2"):
            if(NAND_1["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[9]
            elif(NAND_2["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[10]
            else:
                issue_flag = False
                issue_rs = None
            if(issue_flag):
                issue_rs["Busy"] = "Y"
                issue_rs["Op"] = instruction[0]
                issue_rs["Vj"] = RegFile[instruction[2]]
                issue_rs["Vk"] = RegFile[instruction[3]]
                issue_rs["Qj"] = None
                issue_rs["Qk"] = None
                issue_rs["A"] = None
                issue_rs["Imm"] = None
                if(instruction[2] != "r0" and RegStatus[instruction[2]] != None):
                    issue_rs["Vj"] = None
                    issue_rs["Qj"] = RegStatus[instruction[2]]
                if(instruction[3] != "r0" and RegStatus[instruction[3]] != None):
                    issue_rs["Vk"] = None
                    issue_rs["Qk"] = RegStatus[instruction[3]]
                if(instruction[1] != "r0"):
                    RegStatus[instruction[1]] = issue_rs["Name"]
                current_reservation_stations.append(issue_rs)
                issued.append(instruction)
                execution_time.append(0)
                write_flag.append(False)
        

    elif(instruction[0] == "mul"):
        if(last_written != "MUL"):
            if(MUL["Busy"] == "N"):
                issue_flag = True
                issue_rs = RS[11]
                issue_rs["Busy"] = "Y"
                issue_rs["Op"] = instruction[0]
                issue_rs["Vj"] = RegFile[instruction[2]]
                issue_rs["Vk"] = RegFile[instruction[3]]
                issue_rs["Qj"] = None
                issue_rs["Qk"] = None
                issue_rs["A"] = None
                issue_rs["Imm"] = None
                if(instruction[2] != "r0" and RegStatus[instruction[2]] != None):
                    issue_rs["Vj"] = None
                    issue_rs["Qj"] = RegStatus[instruction[2]]
                if(instruction[3] != "r0" and RegStatus[instruction[3]] != None):
                    issue_rs["Vk"] = None
                    issue_rs["Qk"] = RegStatus[instruction[3]]
                if(instruction[1] != "r0"):
                    RegStatus[instruction[1]] = issue_rs["Name"]
                current_reservation_stations.append(issue_rs)
                issued.append(instruction)
                execution_time.append(0)
                write_flag.append(False)
            else:
                issue_flag = False
                issue_rs = None
               
    return issue_flag

def execute(instruction_position, current_rs, instruction_execution_cycle):
    global total_branches, branch_taken_flag
    global mulV
    global addV, nandV, write_flag, TraceTable

    if(current_rs["Op"] == "load"):
        try:
            if(current_rs["Qj"] is None and instruction_execution_cycle < 6):
                current_rs["Vj"] = RegFile[issued[instruction_position][3]]
                if(instruction_execution_cycle == 0):
                    TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                if(instruction_execution_cycle == 1): #2nd clk cycle in execution
                    current_rs["A"] = current_rs["Vj"] + current_rs["A"]
                if (instruction_execution_cycle == 5):
                    TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                    write_flag[instruction_position] = True
                return (instruction_execution_cycle + 1)
            else:
                return instruction_execution_cycle
        except:
            return instruction_execution_cycle
    elif(current_rs["Op"] == "store"):
        try:
            if(current_rs["Qj"] is None and current_rs["Qk"] is None and instruction_execution_cycle < 6):
                if(instruction_execution_cycle == 0):
                    TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                if(instruction_execution_cycle == 1): #2nd clk cycle in execution
                    current_rs["A"] = current_rs["Vk"] + current_rs["A"]
                if (instruction_execution_cycle == 5):
                    TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                    write_flag[instruction_position] = True
                return (instruction_execution_cycle + 1)
            else:
                return instruction_execution_cycle
        except:
            return instruction_execution_cycle
    elif(current_rs["Op"] == "beq"):
        try:
            if(current_rs["Qj"] is None and current_rs["Qk"] is None and instruction_execution_cycle < 1):
                if(current_rs["Vj"] == current_rs["Vk"]):
                    current_rs["A"] = current_rs["Imm"] + current_rs["A"] + 1
                TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                write_flag[instruction_position] = True
                total_branches += 1
                return (instruction_execution_cycle + 1)
            else:
                return instruction_execution_cycle
        except:
            return instruction_execution_cycle
    elif(current_rs["Op"] == "call"):
        try:
            if(instruction_execution_cycle < 1):
                #current_rs["A"] = current_rs["A"] 
                TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                write_flag[instruction_position] = True
                return(instruction_execution_cycle+1)
            else:
                return(instruction_execution_cycle)
        except:
            return(instruction_execution_cycle)
    elif(current_rs["Op"] == "ret"):
        try:
            if(current_rs["Qj"] is None and instruction_execution_cycle < 1):
                TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                write_flag[instruction_position] = True
                return(instruction_execution_cycle+1)
            else:
                return(instruction_execution_cycle)
        except:
            return(instruction_execution_cycle)
    elif(current_rs["Op"] == "add"):
        try:
            if(current_rs["Qj"] is None and current_rs["Qk"] is None and instruction_execution_cycle < 2):
                if(instruction_execution_cycle == 0):
                    TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                if(instruction_execution_cycle == 1 ):
                    if(current_rs["Name"] == "ADD/ADDI 1"):
                        addV[0] = current_rs["Vj"] + current_rs["Vk"]
                    elif(current_rs["Name"] == "ADD/ADDI 2"):
                        addV[1] = current_rs["Vj"] + current_rs["Vk"]
                    elif(current_rs["Name"] == "ADD/ADDI 3"):
                        addV[2] = current_rs["Vj"] + current_rs["Vk"]
                    else:
                        addV[3] = current_rs["Vj"] + current_rs["Vk"]
                    TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                    write_flag[instruction_position] = True
                return(instruction_execution_cycle+1)
            else:
                return(instruction_execution_cycle)
        except:
            return(instruction_execution_cycle)
    elif(current_rs["Op"] == "addi"):
        try:
            if(current_rs["Qj"] is None and instruction_execution_cycle < 2):
                if(instruction_execution_cycle == 0):
                    TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                if(instruction_execution_cycle == 1):
                    if(current_rs["Name"] == "ADD/ADDI 1"):
                        addV[0] = current_rs["Vj"] + current_rs["Imm"]
                    elif(current_rs["Name"] == "ADD/ADDI 2"):
                        addV[1] = current_rs["Vj"] + current_rs["Imm"]
                    elif(current_rs["Name"] == "ADD/ADDI 3"):
                        addV[2] = current_rs["Vj"] + current_rs["Imm"]
                    else:
                        addV[3] = current_rs["Vj"] + current_rs["Imm"]
                    TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                    write_flag[instruction_position] = True
                return(instruction_execution_cycle+1)
            else:
                return(instruction_execution_cycle)
        except:
            return(instruction_execution_cycle)
    elif(current_rs["Op"] == "nand"):
        try:
            if(current_rs["Qj"] is None and current_rs["Qk"] is None and instruction_execution_cycle < 1):
                if(current_rs["Name"] == "NAND1"):
                    nandV[0] = ~(current_rs["Vj"] & current_rs["Vk"])
                else:
                    nandV[1] = ~(current_rs["Vj"] & current_rs["Vk"])
                TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                write_flag[instruction_position] = True
                return(instruction_execution_cycle+1)
            else:
                return(instruction_execution_cycle)
        except:
            return(instruction_execution_cycle)
    elif(current_rs["Op"] == "mul"):
        try:
            if(current_rs["Qj"] is None and current_rs["Qk"] is None and instruction_execution_cycle < 8):
                if(instruction_execution_cycle == 0):
                    TraceTable[instruction_position]["Execution Start"] = total_clock_cycles
                if(instruction_execution_cycle == 7):
                    mulV= current_rs["Vj"] * current_rs["Vk"]
                    binary_representation = bin(mulV)[2:]
                    if len(binary_representation) > 16:
                        mulV = int(binary_representation[-16:])
                    TraceTable[instruction_position]["Execution End"] = total_clock_cycles
                    write_flag[instruction_position] = True
                return(instruction_execution_cycle+1)
            else:
                return(instruction_execution_cycle)
        except:
            return(instruction_execution_cycle)
    else:
        return None

def empty_rs(rs):
    rs["Busy"] = 'N'
    rs["Op"] = None
    rs["Vj"] = None
    rs["Vk"] = None
    rs["Qj"] = None
    rs["Qk"] = None
    rs["A"] = None
    rs["Imm"] = None

def write(instruction, current_rs, PC):
    global branch_write_flag
    global branch_taken_flag
    global number_of_branch_taken
    global call_ret_write_flag
    global write_val, memory
    pc = PC
    if(current_rs["Op"] == "load"):
        if(instruction[1] != "r0"):
            if(current_rs["Name"] == RegStatus[instruction[1]]):
                RegStatus[instruction[1]] = None
            RegFile[instruction[1]] = memory[current_rs["A"]]
            print("load:",current_rs["A"] , current_rs["Name"], instruction[1])
            write_val = memory[current_rs["A"]]
            print("load:",memory[current_rs["A"]])
        else:
            write_val = 0
        current_rs = empty_rs(current_rs)
    elif(current_rs["Op"] == "store"):
        memory[current_rs["A"]] = current_rs["Vj"]
        print("store:",memory[current_rs["A"]])
        current_rs = empty_rs(current_rs)
        RegStatus[instruction[3]] = None


    elif(current_rs["Op"] == "beq"):
        if(current_rs["Vj"] == current_rs["Vk"]):
            branch_taken_flag = True
            number_of_branch_taken += 1
            pc = current_rs["A"]
        branch_write_flag = True
        current_rs = empty_rs(current_rs)
    elif(current_rs["Op"] == "call"):
        RegFile["r1"] = current_rs["Imm"] + 1
        pc = current_rs["A"] 
        RegStatus["r1"] = None
        call_ret_write_flag = True
        current_rs = empty_rs(current_rs)
    elif(current_rs["Op"] == "ret"):
        pc = current_rs["A"]
        call_ret_write_flag = True
        current_rs = empty_rs(current_rs)
    elif(current_rs["Op"] == "add"):
        if(instruction[1] != "r0"):
            if(current_rs["Name"] == RegStatus[instruction[1]]):
            #     if(current_rs["Name"] == "ADD/ADDI 1"):
            #         RegFile[instruction[1]] = addV[0]
            #     elif(current_rs["Name"] == "ADD/ADDI 2"):
            #         RegFile[instruction[1]] = addV[1]
            #     elif(current_rs["Name"] == "ADD/ADDI 3"):
            #         RegFile[instruction[1]] = addV[2]
            #     else:
            #         RegFile[instruction[1]] = addV[3]
                RegStatus[instruction[1]] = None
            if(current_rs["Name"] == "ADD/ADDI 1"):
                    RegFile[instruction[1]] = addV[0]
                    write_val = addV[0]
            elif(current_rs["Name"] == "ADD/ADDI 2"):
                RegFile[instruction[1]] = addV[1]
                write_val = addV[1]
            elif(current_rs["Name"] == "ADD/ADDI 3"):
                RegFile[instruction[1]] = addV[2]
                write_val = addV[2]
            else:
                RegFile[instruction[1]] = addV[3]
                write_val = addV[3]
        else:
            write_val = 0
        current_rs = empty_rs(current_rs)
    elif(current_rs["Op"] == "addi"):
        if(instruction[1] != "r0"):
            if(current_rs["Name"] == RegStatus[instruction[1]]):
            #     if(current_rs["Name"] == "ADD/ADDI 1"):
            #         RegFile[instruction[1]] = addV[0]
            #     elif(current_rs["Name"] == "ADD/ADDI 2"):
            #         RegFile[instruction[1]] = addV[1]
            #     elif(current_rs["Name"] == "ADD/ADDI 3"):
            #         RegFile[instruction[1]] = addV[2]
            #     else:
            #         RegFile[instruction[1]] = addV[3]
                 RegStatus[instruction[1]] = None
            if(current_rs["Name"] == "ADD/ADDI 1"):
                    RegFile[instruction[1]] = addV[0]
                    write_val = addV[0]
            elif(current_rs["Name"] == "ADD/ADDI 2"):
                    RegFile[instruction[1]] = addV[1]
                    write_val = addV[1]
            elif(current_rs["Name"] == "ADD/ADDI 3"):
                    RegFile[instruction[1]] = addV[2]
                    write_val = addV[2]
            else:
                RegFile[instruction[1]] = addV[3]
                write_val = addV[3]
        else:
            write_val = 0
        current_rs = empty_rs(current_rs)
    elif(current_rs["Op"] == "nand"):
        if(instruction[1] != "r0"):
            if(current_rs["Name"] == RegStatus[instruction[1]]):
                # if(current_rs["Name"] == "NAND1"):
                #     RegFile[instruction[1]] = nandV[0]
                #     write_val = nandV[0]
                # else:
                #     RegFile[instruction[1]] = nandV[1]
                #     write_val = nandV[1]
                RegStatus[instruction[1]] = None
            if(current_rs["Name"] == "NAND1"):
                    RegFile[instruction[1]] = nandV[0]

                    write_val = nandV[0]
            else:
                    RegFile[instruction[1]] = nandV[1]
                    write_val = nandV[1]
        else:
            write_val = 0
        current_rs = empty_rs(current_rs)

    elif(current_rs["Op"] == "mul"):
        if(instruction[1] != "r0"):
            RegFile[instruction[1]] = mulV
            RegStatus[instruction[1]] = None
            write_val = mulV
        else:
            write_val = 0
        current_rs = empty_rs(current_rs)
    return pc

def RS_return_write_values(current_rs, w_val):
    for unit in RS:
        if(unit["Qj"] == current_rs):
            if(unit["Op"]!="load"):
                unit["Qj"] = None
                unit["Vj"] = w_val
            else:
                unit["Qj"] = None
        if(unit["Qk"] == current_rs):
            unit["Qk"] = None
            unit["Vk"] = w_val           


def tomasulo(total_clock_cycles, PC):
    last_written = None

    global cal_ret_stall_issue_flag, branch_instruction_position
    global branch_stall_exec_flag, branch_taken_flag
    global call_ret_write_flag, call_ret_issue_flag
    global  branch_write_flag, branch_issue_flag
    global issued, current_reservation_stations, TraceTable

    cal_ret_stall_issue_flag =  not call_ret_write_flag and call_ret_issue_flag 

    if(not cal_ret_stall_issue_flag):
        call_ret_write_flag = False
        call_ret_issue_flag = False

    branch_stall_exec_flag = not branch_write_flag and branch_issue_flag

    if(not branch_stall_exec_flag):
        branch_write_flag = False
        branch_issue_flag = False
        branch_instruction_position = 100
        branch_taken_flag = False
    
    #check write first
    if(total_clock_cycles > 1): #making sure this happens when clk is more than 1 as writing cant occur yet
        if(len(waiting_for_write) != 0): #something is awaiting its turn for write
            index = waiting_for_write[0] #index of the instruction awaiting write
            last_written = current_reservation_stations[index]["Name"]
            print("last_written: ", last_written)
            NextPC =  write(issued[index], current_reservation_stations[index], PC)
            print("beq",NextPC)
            waiting_for_write.pop(0)
            TraceTable[index]["Write"] = total_clock_cycles

    #execution second
    if(total_clock_cycles != 0): #making sure it is the execution as it can't start with execution
        for i in range(len(current_reservation_stations)):
            if(last_written is not None):
                if(i <= branch_instruction_position):  
                    if(current_reservation_stations[i]["Qj"] != last_written and current_reservation_stations[i]["Qk"] != last_written):
                        execution_time[i] = execute(i, current_reservation_stations[i], execution_time[i])
                        if(write_flag[i]):
                            waiting_for_write.append(i)
                            write_flag[i] = False
            else:
                if(i <= branch_instruction_position):
                    execution_time[i] = execute(i, current_reservation_stations[i], execution_time[i])
                    if(write_flag[i]):
                        waiting_for_write.append(i)
                        write_flag[i] = False
    
    if(last_written is not None  and last_written != "BEQ" and last_written != "CALL/RET"):
        RS_return_write_values(last_written, write_val)
    #issue
    print("now issue",PC)
    if((PC-int(starting_address)) < len(instructions)): #check if there are instructions left to issue
        if(not cal_ret_stall_issue_flag):
            issue_flag = issue(instructions[PC-int(starting_address)],last_written, PC)
             
            if(issue_flag):
                if(instructions[PC-int(starting_address)][0] == "load" or instructions[PC-int(starting_address)][0] == "store"):
                    inst = instructions[PC-int(starting_address)][0]+" "+instructions[PC-int(starting_address)][1] +", "+instructions[PC-int(starting_address)][2] + " (" + instructions[PC-int(starting_address)][3] + ")"
                elif(instructions[PC-int(starting_address)][0] == "call"):
                    inst = instructions[PC-int(starting_address)][0]+" "+instructions[PC-int(starting_address)][1] 
                elif(instructions[PC-int(starting_address)][0] == "ret"):
                    inst = instructions[PC-int(starting_address)][0]
                else:
                    inst = instructions[PC-int(starting_address)][0]+" "+instructions[PC-int(starting_address)][1] +", "+instructions[PC-int(starting_address)][2] + ", " + instructions[PC-int(starting_address)][3] 

                TracingDictionary["Instructions"] = inst
                TracingDictionary["Issue"] = total_clock_cycles
                TraceTable.append(TracingDictionary.copy())
        print("BT", branch_taken_flag)
        if(branch_taken_flag or call_ret_write_flag): #if i am jumping
            cal_ret_stall_issue_flag = False
            call_ret_issue_flag = False
            for inst in range(branch_instruction_position + 1, len(current_reservation_stations)):
                if(issued[inst][0] != "store" and issued[inst][0] != "beq" and issued[inst][0] != "ret"): #the instructions that dont write
                    if(issued[inst][0] == "call"):
                        if(RegStatus["r1"] == "CALL/RET"):
                            RegStatus["r1"] = None
                    elif(RegStatus[issued[inst][1]] == current_reservation_stations[inst]["Name"]):
                        RegStatus[issued[inst][1]] = None
                current_reservation_stations[inst] = empty_rs(current_reservation_stations[inst])
            issued = issued[:branch_instruction_position+1]
            current_reservation_stations = current_reservation_stations[:branch_instruction_position+1]
            TraceTable = TraceTable[:branch_instruction_position+1]
            return NextPC
        elif(cal_ret_stall_issue_flag or not issue_flag):
            return PC
        else:
            return (PC + 1)
    elif(branch_taken_flag  or call_ret_write_flag):
        cal_ret_stall_issue_flag = False
        call_ret_issue_flag = False
        for inst in range(branch_instruction_position + 1, len(current_reservation_stations)):
            if(issued[inst][0] != "store" and issued[inst][0] != "beq" and issued[inst][0] != "ret"): #the instructions that dont write
                if(issued[inst][0] == "call"):
                    if(RegStatus["r1"] == "CALL/RET"):
                        RegStatus["r1"] = None
                elif(RegStatus[issued[inst][1]] == current_reservation_stations[inst]["Name"]):
                    RegStatus[issued[inst][1]] = None
            current_reservation_stations[inst] = empty_rs(current_reservation_stations[inst])
        issued = issued[:branch_instruction_position+1]
        current_reservation_stations = current_reservation_stations[:branch_instruction_position+1]
        TraceTable = TraceTable[:branch_instruction_position+1]
        return NextPC
    else:
        return PC

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
        if (inst[4:6] == '64'):
            return False
        else:
            inst_pattern = re.compile(r'(call)(-?(?:[1-5]?[0-9]|6[0-4]|[0-9]))$')
            matching = inst_pattern.match(inst)
    elif inst[0:3] == 'ret':
        inst_pattern = re.compile(r'(ret)$')
        matching = inst_pattern.match(inst)
    elif inst[0:3] == 'add' or inst[0:3] == 'mul' or inst[0:4] == 'nand':
        inst_pattern = re.compile(r'(add|mul|nand)r[0-7],r[0-7],r[0-7]$')
        matching = inst_pattern.match(inst)
    else:
        matching = False
    return bool(matching)

def stepbystep(next):
    global total_clock_cycles
    global starting_address
    global memory
    PC = int(starting_address)
    while(next == 'y' or next == 'Y'):
        total_clock_cycles += 1
        print("--------------------Tomasulo's Algorithm ------------------")
        
        PC = tomasulo(total_clock_cycles, PC)
        print(PC,"PC")
        print(memory[0])
        print("current clk cycle: ", total_clock_cycles)
        print("\nTracing Table: ")
        print_trace_table()
        print("\nReservation Stations: ")
        print_RS_table()
        print("\n Reagister Status: ")
        print_register_status()
        print("\nRegister File: ")
        print_reg_file()
        print("\n Enter y or Y to see next step anything else to exit: ")
        next = input()
    return


def start():
    global starting_address
    global memory
    print("--------------------Tomasulo's Algorithm ------------------")
    #Memory initialization
    for i in range(64000):
        memory.append(0)
    starting_address = (input("Please enter your starting adress: "))
    while(not(starting_address.isdigit())):
        starting_address = (input("Please enter your starting adress as an integer: "))
    address = 'Y'
    print("Please enter a memory address you want to initialize or exit to cancel: ")
    while address != "exit":
        address = (input("address: "))
        if(address != "exit"):
            data_in = (input("data: "))
            if ((not address.isdigit()) or (not data_in.isdigit()) ):
                print("Invalid address, not allowed")
            else:
                address = int(address)
                data_in = int(data_in)
                if address > 64000 or data_in > 65536 or data_in < 0:
                    print("Invalid range")
                else:
                    memory[address] = data_in
        
        
     
        #new_addr = input("Do you want to add other adresses? (Y/N)")
        #print(new_addr)

    #Instructions intialization and validation

    inst = 'y'
    inst_structured=[] #For applying the different structures of instructions
    print("Please enter the instructions of your program and write exit when you are done: ")
    while inst != "exit":
        inst = (input("insturction: "))
        if(inst != "exit"):
            inst = inst.lower().replace(" ", "")

            if (validation(inst) == False):
                print("Invalid instruction")
            else:
                if(inst[0:4] == 'load'):
                    inst_structured=[inst[0:4],inst[4:6], inst[7:inst.index('(')], inst[inst.index('(')+1:inst.index(')')]]
                elif(inst[0:5] == 'store'):
                    inst_structured = [inst[0:5], inst[5:7], inst[8:inst.index('(')],inst[inst.index('(') + 1:inst.index(')')]]
                elif(inst[0:4] == 'addi' or inst[0:4] == 'nand'):
                    inst_structured = [inst[0:4], inst[4:6], inst[7:9], inst[10:]]
                elif(inst[0:3] == 'beq' or inst[0:3] == 'add' or inst[0:3] == 'mul'):
                    inst_structured = [inst[0:3], inst[3:5], inst[6:8], inst[9:]]
                elif(inst[0:4] == 'call'):
                    inst_structured = [inst[0:4], inst[4:], None, None]
                elif(inst[0:3] == 'ret'):
                    inst_structured = [inst[0:3], None, None, None]
                instructions.append(inst_structured)
        #new_inst = input("Do you want to add other instruction? (Y/N) ")

    stepbystep('y') 
    print("--------------------Additional Information------------------")
    if(total_branches != 0):
        print("\n Branch Misprediction: ", ((number_of_branch_taken)/(total_branches))*100, "%")
    else:
        print("\n no branch instructions were provided")
    
    print("\n total execution time: ", total_clock_cycles)
    print("\n instruction per cycles: ", len(issued)/total_clock_cycles )

start()