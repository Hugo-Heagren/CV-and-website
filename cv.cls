\LoadClass{article}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cv}

% * Packages

\RequirePackage{hyperref}
\RequirePackage[inline]{enumitem}
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
\newcommand{\dategutter}{5em}

% * Style

% No hyphenation. This makes sense because there are no (well, few)
% continuous paragraphs, and hyphenation in lists looks weird.
\raggedright{}

% Hyperlinks are blue (but not TOO blue!)
\hypersetup{
	colorlinks=true, % Colored links
	urlcolor=blue    % Color of external links
}

% ** Fonts

\RequirePackage[T1]{fontenc}
\RequirePackage{libertine}

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
\makeatother

%% Format title
\pretitle{\hspace{\dategutter}\LARGE\bfseries}
\posttitle{\normalfont}

% ** Sections

\titlespacing{\section}{\dategutter}{1ex}{0.5ex}
\titlespacing{\subsection}{\dategutter}{1ex}{0.5ex}
\titlespacing{\subsubsection}{\dategutter}{1ex}{0.5ex}

\newcommand{\secnote}[1]{\textsc{\textnormal{\normalsize{(#1)}}}}

% ** Lists

\setlist[]{
  leftmargin=\dategutter,
  labelwidth=!
}

\setlist[description]{
  font=\normalfont\bfseries\scriptsize\textsc
}

\setlist[itemize]{
  label={}
}

\newlist{areas}{description}{1}
\setlist[areas]{
  style=multiline,
  align=right
}

\newlist{area}{itemize*}{1}
\setlist[area]{
  itemjoin={,\ },
  afterlabel={},
  label={}
}

\newlist{reviews}{itemize*}{1}
\setlist[reviews]{
  itemjoin={,\ },
  afterlabel={},
  label={},
  labelwidth=!,
  labelindent=!,
  labelsep=0pt,
}
