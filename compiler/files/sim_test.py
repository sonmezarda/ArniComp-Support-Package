# Simulate assembly execution
regs = {'ra': 0, 'rd': 0, 'acc': 0, 'marl': 0}
mem = [0] * 256

print('Simulating: (a+b)*3 + 10 where a=10, b=20')
print('Expected result: (10+20)*3 + 10 = 30*3 + 10 = 90 + 10 = 100')
print()

mem[0] = 10  # a @ addr 0
mem[1] = 20  # b @ addr 1

# ldi #10
regs['ra'] = 10
print(f'ldi #10          ra={regs["ra"]}')

# mov rd, ra
regs['rd'] = regs['ra']
print(f'mov rd, ra       rd={regs["rd"]}')

# add ra
regs['acc'] = (regs['rd'] + regs['ra']) & 0xFF
print(f'add ra           acc={regs["acc"]} (rd+ra = {regs["rd"]}+{regs["ra"]})')

# mov rd, acc
regs['rd'] = regs['acc']
print(f'mov rd, acc      rd={regs["rd"]}')

# add ra
regs['acc'] = (regs['rd'] + regs['ra']) & 0xFF
print(f'add ra           acc={regs["acc"]} (rd+ra = {regs["rd"]}+{regs["ra"]}) ; 3*a = 3*10 = 30')

# mov ra, rd
regs['ra'] = regs['rd']
print(f'mov ra, rd       ra={regs["ra"]}')

# add ra
regs['acc'] = (regs['rd'] + regs['ra']) & 0xFF
print(f'add ra           acc={regs["acc"]} (rd+ra = {regs["rd"]}+{regs["ra"]}) ; BUG: should load b here!')

# mov rd, acc
regs['rd'] = regs['acc']
print(f'mov rd, acc      rd={regs["rd"]}')

# add ra
regs['acc'] = (regs['rd'] + regs['ra']) & 0xFF
print(f'add ra           acc={regs["acc"]} (rd+ra = {regs["rd"]}+{regs["ra"]})')

# mov rd, acc
regs['rd'] = regs['acc']
print(f'mov rd, acc      rd={regs["rd"]}')

# add acc
regs['acc'] = (regs['rd'] + regs['acc']) & 0xFF
print(f'add acc          acc={regs["acc"]} (rd+acc = {regs["rd"]}+{regs["acc"]})')

# ldi #10
regs['ra'] = 10
print(f'ldi #10          ra={regs["ra"]}')

# mov rd, acc
regs['rd'] = regs['acc']
print(f'mov rd, acc      rd={regs["rd"]}')

# add ra
regs['acc'] = (regs['rd'] + regs['ra']) & 0xFF
print(f'add ra           acc={regs["acc"]} (rd+ra = {regs["rd"]}+{regs["ra"]}) ; +10')

# ldi #2
regs['ra'] = 2
print(f'ldi #2           ra={regs["ra"]}')

# mov marl, ra
regs['marl'] = regs['ra']
print(f'mov marl, ra     marl={regs["marl"]}')

# mov m, acc
mem[regs['marl']] = regs['acc']
print(f'mov m, acc       mem[{regs["marl"]}] = {regs["acc"]}')

print()
print(f'RESULT: c = {mem[2]}')
print(f'EXPECTED: 100')
print(f'MATCH: {mem[2] == 100}')
