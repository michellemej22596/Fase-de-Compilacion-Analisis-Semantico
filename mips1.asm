.data
newline: .asciiz "\n"
str_0: .asciiz "B is greater than A\n"
str_1: .asciiz "A is greater than B\n"
str_2: .asciiz "A is greater than or equal to B\n"
str_3: .asciiz "A is less than or equal to B\n"
str_4: .asciiz "C is greater than or equal to B\n"
str_5: .asciiz "C is less than or equal to B\n"

.text
.globl main

main:
# (ASSIGN, 5, a)
li $s0, 5

# (ASSIGN, 10, b)
li $s1, 10

# (ASSIGN, 10, c)
li $s2, 10

# (LT, a, b, t0)
slt $t0, $s0, $s1

# (IF_FALSE, t0, L_IF_END_0)
beqz $t0, L_IF_END_0

# (PRINT, "B is greater than A")
la $a0, str_0
li $v0, 4
syscall
la $a0, newline
li $v0, 4
syscall

# (LABEL, L_IF_END_0)
L_IF_END_0:

# (GT, a, b, t1)
slt $t1, $s1, $s0

# (IF_FALSE, t1, L_IF_END_1)
beqz $t1, L_IF_END_1

# (PRINT, "A is greater than B")
la $a0, str_1
li $v0, 4
syscall
la $a0, newline
li $v0, 4
syscall

# (LABEL, L_IF_END_1)
L_IF_END_1:

# (GE, a, b, t2)
slt $t2, $s0, $s1
xori $t2, $t2, 1

# (IF_FALSE, t2, L_IF_END_2)
beqz $t2, L_IF_END_2

# (PRINT, "A is greater than or equal to B")
la $a0, str_2
li $v0, 4
syscall
la $a0, newline
li $v0, 4
syscall

# (LABEL, L_IF_END_2)
L_IF_END_2:

# (LE, a, b, t3)
slt $t4, $s1, $s0
xori $t3, $t4, 1

# (IF_FALSE, t3, L_IF_END_3)
beqz $t3, L_IF_END_3

# (PRINT, "A is less than or equal to B")
la $a0, str_3
li $v0, 4
syscall
la $a0, newline
li $v0, 4
syscall

# (LABEL, L_IF_END_3)
L_IF_END_3:

# (GE, c, b, t4)
slt $t5, $s2, $s1
xori $t5, $t5, 1

# (IF_FALSE, t4, L_IF_END_4)
beqz $t5, L_IF_END_4

# (PRINT, "C is greater than or equal to B")
la $a0, str_4
li $v0, 4
syscall
la $a0, newline
li $v0, 4
syscall

# (LABEL, L_IF_END_4)
L_IF_END_4:

# (LE, c, b, t5)
slt $t7, $s1, $s2
xori $t6, $t7, 1

# (IF_FALSE, t5, L_IF_END_5)
beqz $t6, L_IF_END_5

# (PRINT, "C is less than or equal to B")
la $a0, str_5
li $v0, 4
syscall
la $a0, newline
li $v0, 4
syscall

# (LABEL, L_IF_END_5)
L_IF_END_5:


# Exit program
li $v0, 10
syscall