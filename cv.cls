\LoadClass{article}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cv}

% * Packages

\RequirePackage{hyperref}
\RequirePackage{enumitem}
\RequirePackage{geometry}
\RequirePackage{titlesec}
\RequirePackage{titling}

% * Layout
\geometry{
	a4paper,       % paper size a4
	vmargin=1in,   % 0.5" margins all round
	hmargin=0.8in, % 0.5" margins all round
}

%% Makes absolute formatting much simpler
\setlength{\parindent}{0em}

%% Size of the of the left-hand margin with dates in it
\newcommand{\dategutter}{7em}

% * Style

% Hyperlinks are blue (but not TOO blue!)
\hypersetup{
	colorlinks=true, % Colored links
	urlcolor=blue    % Color of external links
}

% No page numbers
\pagenumbering{gobble}

% ** Fonts

\RequirePackage[T1]{fontenc}
\RequirePackage{kpfonts}

% ** Titles

%% Manually redefine titling's maketitle command to ONLY print the
%% title (not the author or the date)
\makeatletter
\def\@maketitle{%
  \newpage
  \null
  \vskip 2em%
  \vspace*{\droptitle}
  \maketitlehooka
      {\@bspretitle \@title \@bsposttitle}
      \maketitlehookb
          \maketitlehookc
              \maketitlehookd
              \vskip\parskip}
\fi
\makeatother

%% Format title
\pretitle{\hspace{\dategutter}\LARGE\bfseries}
\posttitle{\normalfont}

% ** Sections

\titlespacing{\section}{\dategutter}{1ex}{0.5ex}
\titlespacing{\subsection}{\dategutter}{1ex}{0.5ex}
\titlespacing{\subsubsection}{\dategutter}{1ex}{0.5ex}

% ** Lists

\setlist[]{
  leftmargin=\dategutter,
  labelwidth=!
}

\setlist[description]{
  font=\normalfont\scriptsize\textsc
}

\setlist[itemize]{
  label={}
}

% * ORCID

% This implements the ORCID compact id format:
% https://info.orcid.org/brand-guidelines/#h-compact-orcid-id The
% image was downloaded from:
% https://orcid.figshare.com/articles/figure/ORCID_iD_icon_graphics/5008697?file=8439035
% Technically, the full id would be more appropriate here, but I
% didn't like how it looked. How daring of me!
\DeclareRobustCommand{\orcidcompactlink}[1]{%
  \href{https://orcid.org/#1}%
  {\includegraphics[height=8px]{ORCIDiD_icon24x24.png} #1}}


% Local Variables:
% TeX-master: "cv.tex"
% End:
