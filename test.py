import numpy as np

a = np.random.random(100)
b = np.random.random(100)

c = np.vstack((a, b))

print(a.shape, a.ndim)
print(b.shape, b.ndim)
print(c.shape, c.ndim)