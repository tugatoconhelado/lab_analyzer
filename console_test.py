import numpy as np
import matplotlib.pyplot as plt

a = np.random.random(200)
b = a ** 2
print(a)
plt.plot(a, b, 'bo')
plt.show()