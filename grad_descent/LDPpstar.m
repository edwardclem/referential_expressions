function lambda = LDPpstar(hx, Tx_all, theta, accuracy, lambda)
% Inputs:
    % hx => an (s, 1)-dimensional probability vector
    % Tx => an (s, c)-dimensional vector of sufficient statistics
    % theta => an (s, 1)-dimensional constraint vector
    % accuracy => level of accuracy (e.g. 1e-3)
    
    % Optional Arguments
    % lambda => a value of lambda to start with

if nargin < 5
    c = size(Tx_all{1}, 2);
    lambda = zeros(c, 1);
end
zlambda = get_zlambda(hx, lambda, Tx_all);
expvals = get_expvals(hx, lambda, zlambda, Tx_all);
epsilon = 0.01;

while (norm(expvals - theta) > accuracy)
    disp(norm(expvals - theta))
    lambda = lambda - epsilon*(expvals - theta);
    zlambda = get_zlambda(hx, lambda, Tx_all);
    expvals = get_expvals(hx, lambda, zlambda, Tx_all);
end
end

function expvals = get_expvals(hx, lambda, zlambda, Tx_all)
c = size(Tx_all{1}, 2);
expvals = zeros(c, 1);
num_scenes = length(Tx_all);
for i = 1:num_scenes
    expvals = expvals + sum(Tx_all{i}.*repmat(hx.*exp(Tx_all{i}*lambda)/zlambda(i), 1, c))';
end
expvals = expvals/num_scenes;
end

function zlambda = get_zlambda(hx, lambda, Tx_all)
num_scenes = length(Tx_all);
zlambda = zeros(num_scenes, 1);
for i = 1:num_scenes
    zlambda(i) = sum(exp(Tx_all{i}*lambda).*hx);
end
end

