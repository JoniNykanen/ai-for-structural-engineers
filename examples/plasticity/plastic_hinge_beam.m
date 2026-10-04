% Plastic collapse load of beams via plastic hinges  (MATLAB)
% ===========================================================
% Limit analysis: a beam collapses when enough plastic hinges (each carrying
% the plastic moment Mp) form to turn it into a mechanism. This computes the
% collapse load for three classic cases of span L and plastic moment Mp.
%
% Run in MATLAB, or have Claude run it via the Engine API / MCP server.

% --- Inputs (edit these) ---
Mp = 40;    % plastic moment capacity, kN*m
L  = 6;     % span, m

fprintf('Plastic collapse loads  (Mp = %.1f kN*m, L = %.1f m)\n', Mp, L);
fprintf('--------------------------------------------------------\n');

% 1) Simply supported beam, central point load P.
%    Collapse: one hinge at midspan.  Mp = P*L/4  ->  P = 4*Mp/L
P_ss = 4*Mp / L;
fprintf('Simply supported, central point load:   P = %.2f kN\n', P_ss);

% 2) Fixed-fixed beam, central point load P.
%    Collapse: hinges at both ends + midspan.  P = 8*Mp/L
P_ff = 8*Mp / L;
fprintf('Fixed-fixed, central point load:        P = %.2f kN\n', P_ff);

% 3) Simply supported beam, uniformly distributed load w.
%    Collapse: one hinge at midspan.  Mp = w*L^2/8  ->  w = 8*Mp/L^2
w_ss = 8*Mp / L^2;
fprintf('Simply supported, UDL:                  w = %.2f kN/m\n', w_ss);
fprintf('  (total load = %.2f kN)\n', w_ss*L);

%% Self-check: how to verify the AI's answer
% Check each collapse load with the virtual-work balance of its mechanism
% (external work = internal work, rotation theta = 1, kN*m on both sides):
%   SS point load:  P*(L/2)   = Mp*2          (midspan hinge rotates 2*theta)
%   FF point load:  P*(L/2)   = Mp*(1+2+1)    (end hinges theta, midspan 2*theta)
%   SS UDL:         w*L*(L/4) = Mp*2          (mean deflection under the UDL = L/4)
% Also: the fixed-fixed beam must carry exactly twice the simply supported one.
assert(abs(P_ss*L/2   - 2*Mp) < 1e-9, 'SS point load fails virtual work');
assert(abs(P_ff*L/2   - 4*Mp) < 1e-9, 'FF point load fails virtual work');
assert(abs(w_ss*L*L/4 - 2*Mp) < 1e-9, 'SS UDL fails virtual work');
assert(abs(P_ff/P_ss - 2) < 1e-12, 'fixed-fixed should carry 2x the simply supported load');

fprintf('--------------------------------------------------------\n');
fprintf('Note: plastic (limit) analysis gives the COLLAPSE load. It is higher\n');
fprintf('than the first-yield load for every beam (by the shape factor), and for\n');
fprintf('statically indeterminate beams also by moment redistribution.\n');
