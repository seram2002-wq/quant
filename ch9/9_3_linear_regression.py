# 9.3 텐서플로로 선형 회귀 (책 예제 ch09_08_LinearRegression.py)
# 데이터 (1,2) (2,3) (3,4) (4,5) (5,6)에 가장 잘 맞는 직선 h(x) = w*x + b를 찾는다.
# 정답은 w=1, b=1이고, 처음 값(w=0.7, b=0.7)에서 출발해 조금씩 고쳐 나가는 과정을 본다.
#
# 책은 단계마다 그래프 창을 따로 띄우지만, 여기서는 6개 단계를 한 화면에 모아 그린다.
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # 텐서플로 안내 메시지 줄이기 (import보다 먼저)
from pathlib import Path

import matplotlib.pyplot as plt
import tensorflow as tf

x_data = [1, 2, 3, 4, 5]
y_data = [2, 3, 4, 5, 6]

w = tf.Variable(0.7)            # 기울기 (학습으로 바뀌는 값)
b = tf.Variable(0.7)            # 절편 (학습으로 바뀌는 값)
learn_rate = 0.01               # 학습률: 한 번에 얼마나 크게 고칠지

show_steps = [1, 3, 5, 10, 1000, 1100]
fig, axes = plt.subplots(2, 3, figsize=(13, 8))
axes = iter(axes.flat)

print('step|    w|    b| cost')
print('----|-----|-----|-----')

for i in range(1, 1101):
    # 1) 지금의 w, b로 예측하고, 정답과 얼마나 다른지(비용) 계산
    with tf.GradientTape() as tape:
        hypothesis = w * x_data + b                         # 예측값
        cost = tf.reduce_mean((hypothesis - y_data) ** 2)   # 평균 제곱 오차
    # 2) w, b를 어느 방향으로 고치면 비용이 줄어드는지(기울기) 계산
    dw, db = tape.gradient(cost, [w, b])
    # 3) 그 방향으로 학습률만큼 고침 (경사 하강법)
    w.assign_sub(learn_rate * dw)
    b.assign_sub(learn_rate * db)

    if i in show_steps:
        print(f'{i:4d}| {w.numpy():.2f}| {b.numpy():.2f}| {cost:.2f}')
        ax = next(axes)
        ax.set_title(f'[Step {i:d}]  h(x) = {w.numpy():.2f}x + {b.numpy():.2f}')
        ax.plot(x_data, y_data, 'o')                               # 실제 데이터
        ax.plot(x_data, w * x_data + b, 'r', label='hypothesis')   # 지금의 직선
        ax.set_xlabel('x_data')
        ax.set_ylabel('y_data')
        ax.set_xlim(0, 6)
        ax.set_ylim(1, 7)
        ax.legend(loc='best')

fig.tight_layout()
image_dir = Path(__file__).parent / 'images'
image_dir.mkdir(exist_ok=True)
fig.savefig(image_dir / '9_3.png', dpi=100)      # ch9\images\9_3.png로 저장
plt.show()
