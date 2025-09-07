import os
import sys
import editor


class Compiler:
    def compile_exc1_to_excbite1(exc1_path, bytecode_path):
        with open(exc1_path) as src, open(bytecode_path, "w") as out:
            label_counter = 0
            label_stack = []

            for line in src:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("Display.out("):
                    arg = line[len("Display.out("):-1]
                    out.write(f"LOAD_CONST {arg}\n")
                    out.write("CALL_FUNCTION Display.out\n")

                elif line.startswith("Display.in("):
                    # New logic to handle both with and without a message
                    parts = line[len("Display.in("):-1].split(",", 1)
                    if len(parts) == 2:
                        message = parts[0].strip()
                        var = parts[1].strip()
                        out.write(f"LOAD_CONST {message}\n")
                        out.write(f"CALL_FUNCTION Display.in {var}\n")
                    else:
                        var = parts[0].strip()
                        out.write(f"CALL_FUNCTION Display.in {var}\n")

                elif line == "Display.clear()":
                    out.write("CALL_FUNCTION Display.clear\n")

                elif line.startswith("let "):
                    parts = line[4:].split("=")
                    var = parts[0].strip()
                    expr = parts[1].strip()
                    out.write(f"LOAD_CONST {expr}\n")
                    out.write(f"STORE_NAME {var}\n")

                elif line.startswith("if "):
                    condition = line[3:].strip()
                    label = f"ENDIF_{label_counter}"
                    label_stack.append(label)
                    out.write(f"LOAD_CONDITION {condition}\n")
                    out.write(f"POP_JUMP_IF_FALSE {label}\n")
                    label_counter += 1

                elif line == "else":
                    else_label = f"ELSE_END_{label_counter}"
                    out.write(f"JUMP_FORWARD {else_label}\n")
                    out.write(f"LABEL {label_stack.pop()}\n")
                    label_stack.append(else_label)

                elif line == "endif":
                    out.write(f"LABEL {label_stack.pop()}\n")

                elif line.startswith("while "):
                    condition = line[6:].strip()
                    start_label = f"WHILE_START_{label_counter}"
                    end_label = f"WHILE_END_{label_counter}"
                    label_stack.append((start_label, end_label, condition))
                    out.write(f"LABEL {start_label}\n")
                    out.write(f"LOAD_CONDITION {condition}\n")
                    out.write(f"POP_JUMP_IF_FALSE {end_label}\n")
                    label_counter += 1

                elif line == "endwhile":
                    start_label, end_label, _ = label_stack.pop()
                    out.write(f"JUMP_FORWARD {start_label}\n")
                    out.write(f"LABEL {end_label}\n")

                elif line.startswith("let "):
                    parts = line[4:].split("=")
                    var = parts[0].strip()
                    expr = parts[1].strip()

                    # Detect int() or char() usage
                    if expr.startswith("int(") or expr.startswith("char("):
                        out.write(f"CAST {var} {expr}\n")
                    else:
                        out.write(f"LOAD_CONST {expr}\n")
                        out.write(f"STORE_NAME {var}\n")

                elif line == "end":
                    out.write("END\n")

    def run_excbite1(bytecode_path):
        env = {}
        stack = []
        labels = {}
        instructions = []

        # First pass: load instructions and label positions
        with open(bytecode_path) as f:
            for idx, line in enumerate(f):
                parts = line.strip().split(maxsplit=1)
                if parts[0] == "LABEL":
                    labels[parts[1]] = idx
                instructions.append(line.strip())

        i = 0
        while i < len(instructions):
            parts = instructions[i].split(maxsplit=1)
            instr = parts[0]
            arg = parts[1] if len(parts) > 1 else None

            if instr == "LOAD_CONST":
                stack.append(eval(arg, {}, env))

            elif instr == "STORE_NAME":
                env[arg] = stack.pop()

            elif instr == "LOAD_CONDITION":
                stack.append(eval(arg, {}, env))

            elif instr == "POP_JUMP_IF_FALSE":
                condition = stack.pop()
                if not condition:
                    i = labels[arg]
                    continue

            elif instr == "JUMP_FORWARD":
                i = labels[arg]
                continue

            elif instr == "CALL_FUNCTION":
                if arg == "Display.out":
                    print(stack.pop())
                elif arg.startswith("Display.in"):
                    var = arg.split()[1]
                    # Check if a message is on the stack
                    if stack:
                        message = stack.pop()
                        env[var] = input(f"{message}")
                    else:
                        # Fallback to the old behavior
                        env[var] = input(f"{var}: ")
                elif arg == "Display.clear":
                    print("\033c", end="")

            elif instr == "CAST":
                var, expr = arg.split(maxsplit=1)
                if expr.startswith("int("):
                    inner = expr[4:-1]
                    env[var] = int(eval(inner, {}, env))
                elif expr.startswith("char("):
                    inner = expr[5:-1]
                    env[var] = chr(eval(inner, {}, env))

            elif instr == "END":
                break

            i += 1

    def run_compiler(exc_1_path: str, bytecode_path: str) -> None:
        Compiler.compile_exc1_to_excbite1(exc_1_path, bytecode_path)
        Compiler.run_excbite1(bytecode_path)



class CompilerShell:
    def through_commandline():
        if sys.argv[1] == "Help":
            print("""help manu:
                  
Compilerun : compile the .exc1 and run the .excbite1
Compile : compile the .exc1
Run : run the .excbite1
List : to list the data inside the file
Code : to open a file in the editor""")
        elif sys.argv[1] == "CompileRun":
            Compiler.run_compiler(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "Compile":
            Compiler.compile_exc1_to_excbite1(sys.argv[2])
        elif sys.argv[1] == "Run":
            Compiler.run_excbite1(sys.argv[2])
        elif sys.argv[1] == "List":
            with open(sys.argv[2]) as file:
                print(file.read())

        elif sys.argv[1] == "Code":
            app = editor.CodeEditor()
            app.open_file_shell(sys.argv[2])
            app.mainloop()

    def through_compiler_shell():
        ch = int(input("enter choice:\n1]compile or run\n2] list\n>>>"))

        if ch == 1:
            ch = int(input("enter choice:\n1]compile .exc1\n2]run .excbite1\n3]do both\n>>>"))
            
            if ch == 1:
                ch_exc1 = input("enter exc1 file name\n>>>")
                ch_excbite1 = input("enter excbite1 file name\n>>>")
                Compiler.compile_exc1_to_excbite1(ch_exc1,ch_excbite1)
            elif ch == 2:
                ch_excbite1 = input("enter excbite1 file name\n>>>")
                Compiler.run_excbite1(ch_excbite1)
            elif ch == 3:
                ch_exc1 = input("enter exc1 file name\n>>>")
                ch_excbite1 = input("enter excbite1 file name\n>>>")
                Compiler.compile_exc1_to_excbite1(ch_exc1,ch_excbite1)
                Compiler.run_excbite1(ch_excbite1)
            else: print("invalid")
        elif ch == 2:
            ch = input("enter file name\n>>>")
            with open(ch) as file:
                print(file.read())
        else: print("invalid")
        input()

    def invok_compiler_shell():
        if len(sys.argv) > 1:
            CompilerShell.through_commandline()
        else:
            CompilerShell.through_compiler_shell()


if __name__ == "__main__":
    CompilerShell.invok_compiler_shell()