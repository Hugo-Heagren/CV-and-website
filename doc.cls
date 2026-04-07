\LoadClass{cv}

% Simple class for documents which go alongside my CV, like lists of
% publications or references. Inherits from the CV class, but prints
% the title centred, with my name underneath it (and nothing else).

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{doc}

% Styling stuff; there isn't enough for a separate .cls file to be
% worth it.
\renewcommand\maketitlehooka{\begin{center}\bfseries}
\pretitle{\LARGE}
\posttitle{\par \vskip 1 em}
\renewcommand\maketitlehookb{\authorblock}
\preauthor{\Large}
\postauthor{\par \vskip 1 em}
\renewcommand\maketitlehookd{\end{center}}

% Default to no page numbers, because docs tend to be only one page.
\pagenumbering{gobble}

