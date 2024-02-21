# How to contribute

We welcome third-party patches, which are essential for advancing the science and architecture of Tethys.
But there are a few guidelines that we ask contributors to follow, guidelines that ease the maintainers' organizational and logistical duties, while encouraging development by others.

## Getting Started

* Make sure you have a [GitHub account](https://github.com/signup/free).
* **Open an issue** describing your proposed change or work (after making sure one does not already exist).
  * Clearly describe the issue including steps to reproduce when it is a bug.
  * Discuss how your change will affect Tethys, and thus whether it's MAJOR, MINOR, or a PATCH.
  * Interact with the project maintainers to refine/change/prioritize your issue and identify what branch will be targeted (see below).
* Trivial changes to comments or documentation do not require creating a new issue.

## Making Changes

* **Start your work on the correct branch**.
  * All active devleopment will start off of the `dev` branch.  This represents our next version to be released.  All feature and bug fix branches are to made off of `dev`.
  * If your change is a PATCH, it will typically be based on the current dev branch; if MINOR, the next minor release branch; if MAJOR, the next major release branch. For example, as of this writing there are branches `dev`, `rc1.2` and `rc2.0`, corresponding to the PATCH-MINOR-MAJOR start points respectively.
  * We will never accept pull requests to the `main` branch.
* Make sure your commit messages are descriptive but succinct, describing what was changed and why, and **reference the relevant issue number**. Make commits of logical units.
* Make sure you have added the necessary tests for your changes. Tests should be included in the root `tests` directory and are facilitated using `pytest` which is installed with the development version of Tethys.  See more info on using `pytest` here:  https://docs.pytest.org/en/7.4.x/contents.html
* Run _all_ the tests to assure nothing else was accidentally broken.

## Submitting Changes

* Submit a pull request.
* **Your pull request should include one of the following two statements**:
   * You hereby grant PNNL unlimited license to use your code in this version or any future version of Tethys.
   * Somebody else owns the copyright on the code being contributed (e.g., your employer because you did it as part of your work for them); you are authorized by that owner to grant PNNL an unlimited license to use this code in this version or any future version of Tethys, and you hereby do so. All other rights to the code are reserved by the copyright owner.
* The core team looks at Pull Requests on a regular basis, and will respond as soon as possible.


# Additional Resources

* [General GitHub documentation](http://help.github.com/)
* [GitHub pull request documentation](http://help.github.com/send-pull-requests/)
