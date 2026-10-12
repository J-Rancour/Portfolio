Projects currently working on or worked on
* Chess Engine
[To properly compile on windows
Install MinGW (Install the mingw32-base and the mingw32-gcc-g++ packages. Then set MinGW/bin to env Path), this allows you to run gcc function for compile in make
Install Chocolatey Package Manager (Follow terminal instructions to properly install. Then run Choco install make. Choco should auto add to path but double check)]
  - Full dive introduction into C language
  - First checkpoint will be a functional board for the player
* Educational Prompt Creator
  - Will scrape through educational pdfs to generate a database of questions
  - Questions will be filtered based on education level, subject (literature, science, history, and math [for now]) and type of prompt (if I can narrow it down that well)
  - Frontend will allow person to click which level they like, subject. Prompt will be randomly generated
  - Ideally using AI, can pump out the answer if the person struggles. But will allow it to just tell them they are wrong for now and to try again (Will use SCIPY for mathematical questions, the rest is up for debate)
  - Allow seeding of randomized question sheet in case print outs would like to be made
  - Editorial prompts will be added in case modifications to questions are desired. That will most likely be a seperate prompt, requiring 2 databased
  - 1 database for prefilled questions and another for editorial
* Flashcard Generator
  - Using frontend package of python to quickly develop a japanese flashcard generator
  - Will give options between multiple vocab list
  - Hint preview for each flashcard will include the romanji characters beneath the phrase given to help learning transition
  - OCR will eventually be implemented to find vocab sets from japanese pdfs to enable auto generation of vocab list rather than manually putting them in
* Portfolio Website
  - Multi-page website that will display completed projects and skills
  - Ideally have it connect to other websites that I develop. (Planning on doing chess.com copy as practice after building the engine)
  - Will also have live data displays for stuff I develop eventually. (Most likely Fintech, it's what I know best. But I would love to pivot into physics based or bio based subjects in my own time.)
  - In the future, learn how to properly implement cybersecurity protocols on the website. It may not contain any private info but showcasing those skills would be nice