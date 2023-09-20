"00 00 00 00 00 00 11 22"

string = "005C03005812" # 035C
mask =   "FF0000FFFFFF"
var =    "005F16000000" # 16 5F
hex_string = int(string, 16)
hex_mask = int(mask, 16)
hex_var = int(var, 16)

print('hex_string', hex(hex_string))
print('hex_mask', hex(hex_string))
print('var', hex(hex_var))

tmp = hex_string & hex_mask
print('tmp', hex(tmp))

res = hex_string & hex_mask | hex_var
print('res', hex(res))

