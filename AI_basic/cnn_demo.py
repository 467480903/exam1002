"""A tiny CNN-style convolution and max-pooling demo.

Run with: python3 AI_basic/cnn_demo.py
"""

def convolve_valid(image, kernel):
    """Return a valid, stride-1 2D convolution result."""
    output_height = len(image) - len(kernel) + 1
    output_width = len(image[0]) - len(kernel[0]) + 1
    output = []

    for row in range(output_height):
        output_row = []
        for column in range(output_width):
            value = sum(
                image[row + kernel_row][column + kernel_column]
                * kernel[kernel_row][kernel_column]
                for kernel_row in range(len(kernel))
                for kernel_column in range(len(kernel[0]))
            )
            output_row.append(value)
        output.append(output_row)
    return output


def max_pool_2x2(feature_map):
    """Apply 2x2 max pooling with stride 2."""
    return [
        [max(feature_map[row + inner_row][column + inner_column]
             for inner_row in range(2) for inner_column in range(2))
         for column in range(0, len(feature_map[0]), 2)]
        for row in range(0, len(feature_map), 2)
    ]


def main():
    # A simple 4x4 grayscale image: the bright diagonal is the feature to detect.
    image = [
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 0, 1],
    ]
    diagonal_kernel = [[1, 0], [0, 1]]

    feature_map = convolve_valid(image, diagonal_kernel)
    relu_map = [[max(value, 0) for value in row] for row in feature_map]
    pooled_map = max_pool_2x2(relu_map)

    print("Input image:")
    print(*image, sep="\n")
    print("\nConvolution feature map:")
    print(*feature_map, sep="\n")
    print("\nAfter ReLU:")
    print(*relu_map, sep="\n")
    print("\nAfter 2x2 max pooling:")
    print(*pooled_map, sep="\n")


if __name__ == "__main__":
    main()
