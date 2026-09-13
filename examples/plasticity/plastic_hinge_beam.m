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

fprintf('--------------------------------------------------------\n');
fprintf('Note: plastic (limit) analysis gives the COLLAPSE load, which is\n');
fprintf('higher than the first-yield load for statically indeterminate beams.\n');
