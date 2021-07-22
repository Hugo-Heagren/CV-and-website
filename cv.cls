\LoadClass{article}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cv}

%% * Packages

\RequirePackage{hyperref}
\RequirePackage{enumitem}
\RequirePackage{geometry}
\RequirePackage{titlesec}
\RequirePackage{titling}

%% * Page Layout and style

%% ** Layout
\geometry{
	a4paper,       % paper size a4
	vmargin=1in,   % 0.5" margins all round
	hmargin=0.8in, % 0.5" margins all round
}

%% Makes absolute formatting much simpler
\setlength{\parindent}{0em}

%% Size of the of the left-hand margin with dates in it
\newcommand{\dategutter}{6em}

%% ** Style

% Hyperlinks are blue (but not TOO blue!)
\hypersetup{
	colorlinks=true, % Colored links
	urlcolor=blue    % Color of external links
}

% No page numbers
\pagenumbering{gobble}

%% *** Titles

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
              \par
              \vskip 1.5em}
\fi
\makeatother

%% Format title
\pretitle{\hspace{\dategutter}\LARGE\bfseries}
\posttitle{\normalfont}

%% *** Sections

\titlespacing{\section}{6em}{1ex}{0.5ex}
\titlespacing{\subsection}{6em}{1ex}{0.5ex}
\titlespacing{\subsubsection}{6em}{1ex}{0.5ex}

%% *** Lists

\setlist[]{
  nosep,
  leftmargin=\dategutter
}

\setlist[description]{
  style=nextline,
  font=\normalfont\scriptsize\textsc,
}

\setlist[itemize]{
  label={}
}
