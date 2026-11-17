# 9.1 활성화 함수 (책 예제 ch09_01 ~ ch09_05를 한 파일로 모음)
# 활성화 함수: 뉴런이 받은 입력의 합을 "얼마나 세게 다음으로 전달할지" 정하는 함수.
# 계단, 시그모이드, tanh, ReLU 함수를 그래프로 그리고, 소프트맥스 값을 출력한다.
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def stepfunc(x):
    """계단 함수: 0 이하면 0, 0보다 크면 1 (초기 퍼셉트론에서 사용)"""
    return np.where(x <= 0, 0, 1)


def sigmoid(x):
    """시그모이드 함수: 값을 0~1 사이로 부드럽게 바꿈"""
    return 1 / (1 + np.exp(-x))


def tanh(x):
    """tanh(하이퍼볼릭 탄젠트) 함수: 값을 -1~1 사이로 바꿈"""
    return (np.exp(x) - np.exp(-x)) / (np.exp(x) + np.exp(-x))


def relu(x):
    """ReLU 함수: 0 이하면 0, 0보다 크면 입력값 그대로"""
    return np.maximum(0, x)


def softmax(x):
    """소프트맥스 함수: 여러 값을 합이 1인 확률로 바꿈 (분류 문제의 출력층에서 사용)"""
    return np.exp(x) / np.sum(np.exp(x))


x = np.arange(-10, 10, 0.1)
functions = [('step function', stepfunc), ('sigmoid function', sigmoid),
             ('tanh function', tanh), ('ReLU function', relu)]

fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, (title, func) in zip(axes.flat, functions):
    ax.plot(x, func(x))
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
fig.tight_layout()

# 그래프를 ch9\images\9_1.png로 저장
image_dir = Path(__file__).parent / 'images'
image_dir.mkdir(exist_ok=True)
fig.savefig(image_dir / '9_1.png', dpi=100)

# 소프트맥스: 입력이 클수록 확률이 커지고, 전체 합은 1이 된다
a = np.array([0.3, 2.9, 4.0])
y = softmax(a)
print('softmax 입력 :', a)
print('softmax 출력 :', np.round(y, 4))
print('출력의 합    :', round(float(np.sum(y)), 4))

plt.show()
