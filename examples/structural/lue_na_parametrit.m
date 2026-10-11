function p = lue_na_parametrit(pakolliset, polku)
%LUE_NA_PARAMETRIT  Lue normiarvot params/na_timber.yaml -tiedostosta MATLAB-structiksi.
%
%   p = lue_na_parametrit()                   lukee <repo>/params/na_timber.yaml
%   p = lue_na_parametrit(pakolliset)         ... ja pysähtyy, jos jokin
%                                             pakollisista kentistä puuttuu tai on tyhjä
%   p = lue_na_parametrit(pakolliset, polku)  lukee annetun tiedoston
%
%   pakolliset: string-taulukko pisteellä erotettuja polkuja, esim.
%   ["material.f_m_k", "actions.gamma_G_610a"]. Moduuli ei arvaa normiarvoja.
%
%   Normiarvoja (gamma-kertoimet, k_mod, psi, lujuudet...) ei kirjoiteta tähän
%   repoon — ne ovat CEN:n / SFS:n tekijänoikeuden alaisia. Käyttäjä täyttää ne
%   omasta lisensoidusta normistaan tiedostoon params/na_timber.yaml (gitignored),
%   pohjana params/na_timber.example.yaml. Sama tiedosto kuin Python-esimerkissä
%   examples/eurocode/timber/glulam_beam_ec5.py.
%
%   YAML luetaan MATLABin Python-rajapinnan kautta (pyyaml). Jos Python ei ole
%   vielä ladattu, käytetään repon .venv-ympäristöä (setup.ps1 / setup.sh luo sen).

repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
if nargin < 1
    pakolliset = strings(0);
end
if nargin < 2
    polku = fullfile(repo, 'params', 'na_timber.yaml');
end
if ~isfile(polku)
    error('lue_na_parametrit:puuttuu', ...
        ['Parametritiedostoa ei löydy: %s\nKopioi params/na_timber.example.yaml -> ' ...
         'params/na_timber.yaml ja täytä arvot lisensoidusta normistasi.'], polku);
end

pe = pyenv;
if pe.Status == "NotLoaded"
    for venv = {fullfile(repo, '.venv', 'Scripts', 'python.exe'), fullfile(repo, '.venv', 'bin', 'python')}
        if isfile(venv{1})
            pyenv('Version', venv{1});
            break
        end
    end
end
try
    yaml = py.importlib.import_module('yaml');
catch
    error('lue_na_parametrit:pyyaml', ...
        ['pyyaml puuttuu MATLABin käyttämästä Pythonista (%s).\n' ...
         'Aja setup.ps1 / setup.sh tai: <python> -m pip install pyyaml'], string(pyenv().Executable));
end
p = py2mat(yaml.safe_load(fileread(polku)));

for kentta = string(pakolliset)
    solmu = p;
    for avain = split(kentta, ".")'
        if ~isstruct(solmu) || ~isfield(solmu, avain) || isempty(solmu.(avain))
            error('lue_na_parametrit:arvo', ...
                'Puuttuva arvo: ''%s''. Täytä params/na_timber.yaml. Moduuli ei arvaa normiarvoja.', kentta);
        end
        solmu = solmu.(avain);
    end
end
end

function m = py2mat(x)
% Muunna pyyamlin tulos (dict / float / int / str / None) MATLAB-tyypeiksi.
if isa(x, 'py.dict')
    m = struct();
    avaimet = cell(py.list(x.keys()));
    for i = 1:numel(avaimet)
        m.(char(avaimet{i})) = py2mat(x.get(avaimet{i}));
    end
elseif isa(x, 'py.float') || isa(x, 'py.int') || isa(x, 'py.bool')
    m = double(x);
elseif isa(x, 'py.str')
    m = string(x);
elseif isa(x, 'py.NoneType')
    m = [];
else
    m = x;
end
end
