"""A tiny RNN forward-pass demo.

Run with: python3 AI_basic/rnn_demo.py
"""

from math import tanh


def main():
    # Each number is one time step in a short sequence.
    sequence = [0.2, 0.7, -0.1, 0.5]

    # Fixed weights keep the example deterministic.  A real model learns them.
    weight_input = [0.8, -0.4]
    weight_hidden = [[0.3, 0.1], [-0.2, 0.5]]
    bias = [0.0, 0.1]

    hidden = [0.0, 0.0]
    print("RNN hidden states")
    for time_step, value in enumerate(sequence, start=1):
        # h_t = tanh(x_t * W_xh + h_(t-1) * W_hh + b)
        hidden = [
            tanh(value * weight_input[column]
                 + hidden[0] * weight_hidden[0][column]
                 + hidden[1] * weight_hidden[1][column]
                 + bias[column])
            for column in range(2)
        ]
        rounded_hidden = [round(number, 3) for number in hidden]
        print(f"step {time_step}, input={value:.1f}, hidden={rounded_hidden}")

    print("\nFinal hidden state (a compact summary of the sequence):",
          [round(number, 3) for number in hidden])


if __name__ == "__main__":
    main()
