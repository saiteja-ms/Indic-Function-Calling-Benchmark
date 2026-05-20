
I’m a bandit
Random topics in optimization, probability, and statistics. By Sébastien Bubeck
ORF523: The complexities of optimization
Guest posts
Archives
About me

ORF523: Classification, SVM, Kernel Learning
Posted on February 26, 2013 by Sebastien Bubeck
In this post I will go over some simple examples of applications for the optimization techniques that we have seen in the previous lectures. The general theme of these examples is the canonical Machine Learning problem of classification. Since the focus here is on optimization I will not discuss the strong interplay between the design of the optimization problems and their statistical properties in terms of generalization error. The interested reader is referred to the book ‘Learning with Kernels’ by Schölkopf and Smola, and the paper ‘Learning the kernel matrix with semi-definite programming’ by Lanckriet, Cristianini, Bartlett, El Ghaoui and Jordan.

Linear classification

Let $(x_1, y_1), \hdots, (x_m, y_n) \in {\mathbb R}^n \times \{-1,1\}$ be a ‘labeled’ data set. Imagine for instance that $x_i$ is a picture, and $y_i$ is equal to $1$ if the picture contains an apple. Our goal is to construct a map (or a classifier) from ${\mathbb R}^n$ to $\{-1,1\}$ that correctly classifies our data set. We restrict our attention to linear classifiers of the form $x \mapsto \mathrm{sgn}(w^{\top} x + b)$. In other words we are looking for a separating hyperplane between $\{x_i : y_i =1\}$ and $\{x_i : y_i = -1\}$. Let us assume that such an hyperplane exists, we say that the data is linearly separable.

For several reasons it seems reasonable to search for the hyperplane that maximizes the margin, that is that maximizes the distance between the hyperplane and its closest data points. Up to renormalization one can assume that for all points one has $|w^{\top} x_i + b| \geq 1$, in which case a quick picture shows that the margin is proportional to $1 / \|w\|^2$. Thus we arrive at the following optimization problem:


\displaystyle \begin{array}{rcl} & \min_{(w,b) \in {\mathbb R}^n \times {\mathbb R}} & \|w\|^2 \\ & \text{subject to} & y_i(w^{\top} x_i + b) \geq 1, i =1, \hdots, m . \end{array} 


This problem can be efficiently solved with Interior Point Methods. It is a Quadratic Program with linear constraints.

Support Vector Machine (SVM)

Let us look at the Lagrangian for the linear classification problem described above:


\displaystyle L(w, b, \lambda) = \frac12 \|w\|^2 - \sum_{i=1}^m \lambda_i (y_i(w^{\top} x_i + b) -1) , \qquad \lambda \in {\mathbb R}_+^m .


Since strong duality clearly holds true for this problem (see previous post), one has by the KKT conditions that at the optimum $(w^*, b^*)$ for the primal, there exists $\lambda^* \in {\mathbb R}^m_+$ (a solution to the dual problem) such that


\displaystyle w^* - \sum_{i=1}^m \lambda_i^* y_i x_i = 0 \ \ \ \ \ (1)




\displaystyle \sum_{i=1}^m \lambda_i^* y_i = 0 \ \ \ \ \ (2)




\displaystyle \lambda_i^* (y_i({w^*}^{\top} x_i + b^*) -1) = 0, i =1, \hdots, m . \ \ \ \ \ (3)


The last equation (3) states that at any point $x_i$ which is not on the boundary of decision the corresponding Lagrange multiplier $\lambda_i^*$ must be equal to $0$. The points $x_i$ on the boundary of decision are calledsupport vectors. In particular, given equation (1) one can see that in fact the optimal classifier depends only on these support vectors, as $w^* = \sum_{i=1}^m \lambda_i^* y_i x_i$, hence the name Support Vector Machine.

Another consequence of (1) is that the solution to the primal problem can be immediately obtained from the solution of the dual problem. Since the KKT conditions are necessary and sufficient for optimality (by convexity), we can restrict our search over $(w,b, \lambda)$ that satisfies equations (1)–(2)–(3). In particular the dual problem can now be written as:


\displaystyle \begin{array}{rcl} & \max_{\lambda \in {\mathbb R}_+^m} & \frac12 \| w \|^2 - \sum_{i=1}^m \lambda_i (y_i w^{\top} x_i -1) \\ & \text{subject to} & \sum_{i=1}^m \lambda_i y_i = 0 \;\; \text{and} \;\; w = \sum_{i=1}^m \lambda_i y_i x_i . \end{array} 


A simple rewriting now yields the standard dual form of the SVM, with $e=(1, \hdots, 1) \in {\mathbb R}^m$, $K \in {\mathbb R}^{m \times m}$ the Gram matrix defined by $K_{i,j} = x_i^{\top} x_j$, and $A \circ B$ the Hadamard product between two matrices,


\displaystyle \begin{array}{rcl} & \max_{\lambda \in {\mathbb R}_+^m} & \lambda^{\top} e - \frac12 \lambda^{\top} (K \circ y y^{\top}) \lambda \\ & \text{subject to} & \lambda^{\top} y = 0 . \end{array} 


The kernel trick

In the dual formulation of the SVM it happens that the original data $x_1, \hdots, x_m \in {\mathbb R}^n$ only appears in the form of the Gram matrix $K$. The kernel trick consists in replacing the Gram matrix in the original space by the Gram matrix in a potentially much higher dimensional space. Formally one considers a mapping $\Phi$ from the original space of data $\mathcal{X}$ ($\mathcal{X} ={\mathbb R}^n$ in our example so far, but more generally it could be an arbitrary set) to some Hilbert space $\mathcal{H}$. Then the Gram matrix $K$ is computed in the feature space $\mathcal{H}$, that is $K_{i,j} = \langle \Phi(x_i), \Phi(x_j) \rangle$. Solving the (dual) SVM with this Gram matrix then gives a linear classifier in the feature space, which when viewed in the original space might be highly non-linear.

What is important to understand is that one does not need to compute the mapping $\Phi$, but only inner products of the form $\langle \Phi(x), \Phi(x') \rangle$. In many interesting cases the latter operation is much cheaper, and it makes sense to focus the method around this last object. The idea is that it suffices to have a kernel $k: \mathcal{X} \times \mathcal{X} \rightarrow {\mathbb R}$ such that for any $x_1, \hdots, x_m$ the kernel Gram matrix $K_{i,j} = k(x_i, x_j)$ is positive definite. We call such a kernel a positive definite kernel. Typical examples on $\mathcal{X} \subset {\mathbb R}^n$ are the polynomial kernel $k_d(x, x') = (x^{\top} x')^d$, and the Gaussian kernel $k_{\sigma}(x, x') = \exp\left( - \frac{1}{2 \sigma^2} \|x - x'\|^2\right)$.

Kernel learning

A natural idea is to put the kernel Gram matrix as part of the objective, in order to maximize the resulting margin. This leads to the following optimization problem


\displaystyle \begin{array}{rcl} & \min_{K \succ 0} \max_{\lambda \in {\mathbb R}_+^m} & \lambda^{\top} e - \frac12 \lambda^{\top} (K \circ y y^{\top}) \lambda \\ & \text{subject to} & \lambda^{\top} y= 0 . \end{array} 


We show now how to express the above problem as an SDP. The idea is apply the KKT conditions and strong duality to transform the maximization problem (over $\lambda$) into a minimization problem. Let us see how this works. First we consider the Lagrangian associated with the maximization problem:


\displaystyle L(\lambda, \alpha, \nu) = \lambda^{\top} e - \frac12 \lambda^{\top} (K \circ y y^{\top}) \lambda + \nu \lambda^{\top} y + \alpha^{\top} \lambda .


The KKT conditions shows that at the optimum, one has (note that $K \circ y y^{\top} \succ 0$ and thus it is invertible)


\displaystyle \lambda^* = (K \circ y y^{\top})^{-1} (e + \nu^* y + \alpha^*) .


Thus the dual of the maximization problem above can be written as


\displaystyle \min_{\nu \in {\mathbb R}, \alpha \in {\mathbb R}_+^m} L\bigg((K \circ y y^{\top})^{-1} (e + \nu y + \alpha), \alpha, \nu\bigg) = \min_{\nu \in {\mathbb R}, \alpha \in {\mathbb R}_+^m} \frac12 (e + \nu y + \alpha) (K \circ y y^{\top})^{-1} (e + \nu y + \alpha) .


Finally we use Schur complement lemma to write this minimization into the constraints as an SDP.

Lemma 1 (Schur complement) Let


\displaystyle X = \left( \begin{array}{cc} A & B \\ B^{\top} & C \end{array} \right) ,


where $A$ is positive definite. Then $X$ is positive semi-definite if and only if $C - B^{\top} A^{-1} B$ (the Schur complement of $A$ in $X$) is positive semi-definite.

In our case we use this lemma to write


\displaystyle t \geq \frac12 (e + \nu y + \alpha) (K \circ y y^{\top})^{-1} (e + \nu y + \alpha) \Leftrightarrow \left( \begin{array}{cc} K \circ y y^{\top} & e + \nu y + \alpha \\ (e + \nu y + \alpha)^{\top} & 2 t \end{array} \right) \succeq 0 .


Putting everything together we have proved that our original problem is equivalent to:


\displaystyle \begin{array}{rcl} & \min_{K, t, \alpha, \nu} & t \\ & \text{subject to} & \left( \begin{array}{cccc} K & 0 & 0 & 0 \\ 0 & \mathrm{diag}(\alpha) & 0 & 0 \\ 0 & 0 & K \circ y y^{\top} & e + \nu y + \alpha \\ 0 & 0 & (e + \nu y + \alpha)^{\top} & 2t \end{array} \right)\succeq 0 , \end{array} 


which is clearly an SDP with equality constraints. Note that for statistical reasons one usually adds a constraint of the form $\mathrm{Tr}(K) \leq c$ (for some fixed constant $c > 0$) in the above optimization problem.
