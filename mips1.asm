.data
newline: .asciiz "\n"

.text
.globl main

main:
# (LABEL, L_FUNC_ADD_0)
L_FUNC_ADD_0:

# (BEGIN_FUNC, add, 2)
# Function: add
add:
# Function prologue
addi $sp, $sp, -8
sw $ra, 4($sp)
sw $fp, 0($sp)
move $fp, $sp
addi $sp, $sp, -32

# (ADD, a, b, t0)
add $t0, $s0, $s1

# (RETURN, t0)
move $v0, $t0
# Early return
move $sp, $fp
lw $fp, 0($sp)
lw $ra, 4($sp)
addi $sp, $sp, 8
jr $ra

# (END_FUNC, add)
# End function: add
# Function epilogue
move $sp, $fp
lw $fp, 0($sp)
lw $ra, 4($sp)
addi $sp, $sp, 8
jr $ra

# (PARAM, 2)
li $t1, 2
move $a0, $t1

# (PARAM, 3)
li $t2, 3
move $a1, $t2

# (CALL, add, 2, t0)
jal add
move $t0, $v0

# (ASSIGN, t0, x)
move $s2, $t0


# Exit program
li $v0, 10
syscall