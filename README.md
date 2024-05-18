# Tomasulo-Simulator
Computer Architecture, Project 2

**Introduction:**
The objective of this project is to construct one of the main concepts taken in our course, Instruction-Level-Parallelism, also known as the ability to execute multiple instructions simultaneously and in our case on a single-issue processor through Tomosulo’s Algorithm. Therefore, this project implements a simulator using this algorithm which allows dynamic scheduling through out-of-order execution whilst taking into account any potential data dependencies and hazards. In the given program,  it only supports 9 basic instructions of risc-v, which are load,store, call,return,add,addi,mul, and nand using python code. We implemented this program by adding different functions for each stage issue, execution, and write ; in addition, we added extra functions for other requirements which are needed in these stages, for the validation, and for combining everything together. The bonus chosen was to take advantage of the tables outputted by giving the user the option to track the changes step by step, however we did not implement a GUI and instead we made the output in the console in a user-friendly way as it is not only useful for anyone running the program,bu:t also for us when debugging and making sure that everything’s in place.

**Walkthrough the code:**
-Using global variables to be able to save any change throughout different stages simeltanously
-Using flags to be able to stall if needed in the known special cases such as beq, call, and return encountered in the algorithm
-Using dictionary for the reservation station
-start function takes the input from the user and makes sure its valid by sending it to the validation function
-validation function makes sure that all the instructions are within their correct format and that the sizes of the immediates/offsets are within a given range
-print_RS_table prints the reservation station table
-print_trace_table prints the trace table
-print_register_status prints register status
-print_reg_file prints register file
-empty_rs which initialzes all the values in the reservation station to None
Stages is divided into these functions : 
1- issue : takes in instruction currently being executed, the last_written to be able to track the reservation stations being written to, and the PC. This function checks first if it can issue by trying to find an empty reservation station, and when it does it initializes the needed entries of the tracing table accordingly whilst checking if there is any data dependencies to be handled. Lastly, we send the issue flag.
2- execution: takes in instruction_position to be able to track which elements as the execution is out of order, current_rs , and instruction_execution_cycle to be updated. This function handles each instruction differently according to the functionality it does along with the different cycles it takes to finish. According to the cycles it takes, we initiate the values of the execution start and end and in between them we apply the functionality needed (if it takes more than one cycle) and at the last cycle we give the signal to start writing. All of this while taking into consederation different reservation stations using if statments and lists to be able to track which one is currently used. Lastly, we return instruction execution cycle.
3- write: takes in instruction currently being executed , current_rs being used, and PC. This function checks the instruction, any existing dependency and makes sure that the

