def arithmetic_arranger(problems, ans = False):
  
  errors =\
  {
    'OpErr': 'Error: Operator must be "+" or "-"', 
    'NumErr': 'Error: Numbers must only contain digits.',
    'LenErr': 'Error: Number cannot be more than four digits',
    'ManyErr': 'Error: Too many problems.',
    'BadErr': 'Sumting Wong!'
  }  

  topRow = []
  botRow = []
  formatW = []
  pTotal = []
  combo = []
  symbol = []
  
  if len(problems) > 5:
    return errors['ManyErr']
  else: 
    for ops in problems:
      try:
        [op1, operator, op2] = ops.split()
        topRow.append(op1)
        symbol.append(operator)
        botRow.append(op2)
      except ValueError: 
        return errors['BadErr'] 

  if operator not in "+=":
    return errors['OpErr']
  elif len(op1) > 4 or len(op2) > 4:
    return errors['LenErr']
  elif not op1.isdigit() or not op2.isdigit():
    return errors['NumErr']

  a = 0
  while a < len(problems):
    formatW.append(max(len(topRow[a]), len(botRow[a])))
    a += 1
  b = 0 
  while b < len(problems): 
    if symbol[b] == '+': 
      pTotal.append(int(topRow[b]) + int(botRow[b]))
    else: 
      pTotal.append((int(topRow[b]) - int(botRow[b])))
    b += 1
  c = 0 
  for optr in topRow: 
    if optr != topRow[-1] or c != len(topRow) - 1: 
      combo.append(topRow[c].rjust(formatW[c] + 2) + '   ')
    else: 
      combo.append((topRow[c].rjust(formatW[c] + 2)) + '\n')
    c += 1
  d = 0 
  for optr in botRow: 
    if optr != botRow[-1] or d != len(botRow) - 1: 
      combo.append(symbol[d] +''+ botRow[d].rjust(formatW[d]) +\
                   '  ')
    else:
      combo.append(symbol[d] + '' + botRow[d].rjust(formatW[d]) + '\n')
    d += 1
    
  e = 0 
  while e < len(pTotal):
    if e != len(pTotal) -1: 
      combo.append('-'*(formatW[e] + 2) + '   ')
    elif ans is True: 
      combo.append('-'*(formatW[e] + 2) + '\n')
    else: 
      combo.append('-'*(formatW[e] + 2))
    e += 1

  if ans is True: 
    f = 0
    for num in pTotal: 
      if num != pTotal[-1]:
        combo.append(str(pTotal[f]).rjust(formatW[f]+2)+'  ')
      else: 
        combo.append(str(pTotal[f]).rjust(formatW[f] + 2))
      f += 1

  g = 0 
  while g < len(combo): 
    combo[g]
    g += 1

  convert = ''.join(combo)
  return convert
  return arithmetic_arranger
