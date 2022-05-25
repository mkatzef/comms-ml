## Regions

### 1
Router MAC: 2e:a6:0c:f2:2c:40
N devices: 10
Comm types: wifi, UDP
Comm patterns: bursty, low

### 2
Router MAC: 6b:f7:ed:31:0a:e9
N devices: 20
Comm types: wifi, UDP
Comm patterns: bursty, low, and hawkes low

### 3
Router MAC: 31:a5:26:5e:a7:aa
N devices: 15
Comm types: wifi, UDP
Comm patterns: bursty, low, and hawkes high

### 4
Router MAC: 50:75:b7:f8:f3:7a
N devices: 5
Comm types: wifi, UDP
Comm patterns: bursty, high, and hawkes high


# Utils
```
def get_mac():
    return ':'.join('%02x' % random.randint(0, 255) for _ in range(6))
```
