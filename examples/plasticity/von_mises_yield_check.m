% von Mises & Tresca yield check  (MATLAB)
% =========================================
% MATLAB equivalent of von_mises_yield_check.py.
% Run in MATLAB, or have Claude run it via the Engine API / MCP server.

%% Self-check: how to verify the AI's answer
% Test the formulas on stress states with a known textbook answer first:
%   uniaxial sigma -> von Mises = sigma;  pure shear tau -> von Mises = sqrt(3)*tau,
%   Tresca = 2*tau;  hydrostatic pressure -> 0 (no yielding).
% If a known case fails, do not trust the result for your real problem.
vmOf     = @(S) sqrt(0.5*sum((sort(eig(S)) - circshift(sort(eig(S)), 1)).^2));
trescaOf = @(S) max(eig(S)) - min(eig(S));
tau_chk  = 50;
assert(abs(vmOf(diag([100 0 0])) - 100) < 1e-9, 'uniaxial: von Mises should equal sigma');
assert(abs(vmOf([0 tau_chk 0; tau_chk 0 0; 0 0 0]) - sqrt(3)*tau_chk) < 1e-9, ...
       'pure shear: von Mises should equal sqrt(3)*tau');
assert(abs(trescaOf([0 tau_chk 0; tau_chk 0 0; 0 0 0]) - 2*tau_chk) < 1e-9, ...
       'pure shear: Tresca should equal 2*tau');
assert(vmOf(-80*eye(3)) < 1e-9, 'hydrostatic stress must give zero von Mises stress');
clear vmOf trescaOf tau_chk

% --- Inputs (edit these) ---
sigma = [180  40   0;
          40  60   0;
           0   0   0];   % Cauchy stress tensor, MPa
sigma_y = 250;           % yield strength, MPa

% Principal stresses = eigenvalues of the symmetric stress tensor.
principal = sort(eig(sigma), 'descend');   % s1 >= s2 >= s3
s1 = principal(1); s2 = principal(2); s3 = principal(3);

% von Mises equivalent stress.
von_mises = sqrt(0.5*((s1-s2)^2 + (s2-s3)^2 + (s3-s1)^2));

% Tresca equivalent stress = s1 - s3.
tresca = s1 - s3;

% Factors of safety.
n_vm     = sigma_y / von_mises;
n_tresca = sigma_y / tresca;

fprintf('=== von Mises / Tresca yield check ===\n');
fprintf('Principal stresses:  s1=%8.2f  s2=%8.2f  s3=%8.2f  MPa\n', s1, s2, s3);
fprintf('von Mises stress:    %8.2f MPa\n', von_mises);
fprintf('Tresca stress:       %8.2f MPa\n', tresca);
fprintf('Yield strength:      %8.2f MPa\n', sigma_y);
fprintf('----------------------------------------\n');
fprintf('Factor of safety (von Mises): %.3f\n', n_vm);
fprintf('Factor of safety (Tresca):    %.3f\n', n_tresca);
fprintf('----------------------------------------\n');
if von_mises >= sigma_y
    fprintf('Result (von Mises): YIELDING\n');
else
    fprintf('Result (von Mises): SAFE (elastic)\n');
end
