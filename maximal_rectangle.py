class Solution:
    """
    @param matrix: a boolean 2D matrix
    @return: an integer
    [
        [1,1,0,0,1],
        [0,1,0,0,1],
        [0,0,1,1,1],
        [0,0,1,1,1],
        [0,0,0,0,1]
    ]
    
    [
        [0,0,0,0,1,1,0,0,1,0],
        [0,1,1,1,0,0,1,0,1,1],
        [1,1,0,1,1,0,1,0,0,0],
        [0,1,0,0,1,1,0,0,1,1],
        [0,1,1,1,0,1,0,1,1,1],
        [0,0,1,0,0,0,0,1,0,1],
        [1,1,0,1,1,1,0,1,1,1],
        [1,1,0,0,1,0,1,1,1,0],
        [0,0,0,1,0,0,0,1,1,0],
        [0,0,1,0,1,1,1,1,0,1],
        [0,1,0,0,1,1,0,0,0,0],
        [0,1,0,1,0,0,1,0,1,1],
        [1,1,1,0,1,1,1,1,0,0],
        [0,1,1,0,1,1,0,0,1,0],
        [0,0,1,0,1,0,0,0,0,0],
        [1,1,1,1,0,1,0,1,0,0],
        [1,0,1,1,0,1,0,0,1,1],
        [1,1,1,0,1,0,0,1,1,1],
        [1,0,0,1,1,0,0,1,0,0]]
    """
    def maximalRectangle(self, matrix):
        def max_area_histogram(hist):
            if not hist:
                return 0
            max_area = 0
            stack = []
            i = 0
            while i < len(hist):
                if not stack or hist[i] >= hist[stack[-1]]:
                    stack.append(i)
                    i+=1
                else:
                    h = hist[stack.pop()]
                    area = h*i if not stack else h*(i-stack[-1] - 1)
                    
                    if area > max_area:
                        max_area = area

            while stack:
                h = hist[stack.pop()]
                area = h*i if not stack else h*(i-stack[-1] - 1)
                if area > max_area:
                    max_area = area
                        
            return max_area
        
        #construct histogram
        if not matrix:
            return 0
        n = len(matrix)
        m = len(matrix[0])
        hist = [0 for i in range(len(matrix[0]))]
        max_area = 0
        for i in range(n):
            for j in range(m):
                if matrix[i][j] == 0:
                    hist[j] = 0
                else:
                    hist[j] += 1
            area = max_area_histogram(hist)
            if area > max_area:
                max_area = area
        return max_area