#!/bin/bash -x
GIT_DIR=$PWD/batch_search/frh-A4
TMP_DIR=$PWD/batch_search/frh-A4/tmp
#ITER=10000
ITER=100
PRECISION=13
SYMMETRY=A4
SEARCH_SCRIPT=roots.batch.py
FILTER_SCRIPT=filter.py

DYN_A4_FILES="frh-roots-0_1_0_1_1_0_1-fld_shell.0-shell_1_loose-opp_shell_1_loose.py
 frh-roots-0_1_0_1_1_0_1-fld_w.0-shell_1_loose-opp_shell_1_loose.py
 frh-roots-0_1_1_0_1_1_0-fld_w.0-shell_1_loose-opp_shell_1_loose.py
 frh-roots-0_1_1_0_1_1_0-fld_w.0-shell_1_loose-opp_strip_1_loose.py
 frh-roots-0_1_1_0_1_1_0-fld_w.0-strip_1_loose-opp_shell_1_loose.py
 frh-roots-0_1_1_0_1_1_0-fld_w.0-strip_1_loose-opp_strip_1_loose.py
 frh-roots-0_V2_1_0_V2_1_0-fld_w.0-alt_strip_1_loose-opp_alt_strip_1_loose.py
 frh-roots-0_V2_1_0_V2_1_0-fld_w.0-shell_1_loose-opp_shell_1_loose.py
 frh-roots-0_V2_1_0_V2_1_0-fld_w.0-shell_1_loose-opp_strip_1_loose.py
 frh-roots-0_V2_1_0_V2_1_0-fld_w.0-strip_1_loose-opp_shell_1_loose.py
 frh-roots-0_V2_1_0_V2_1_0-fld_w.0-strip_1_loose-opp_strip_1_loose.py
"

for DIR in $GIT_DIR $TMP_DIR ; do {
	if [ ! -d "$DIR" ] ; then {
		mkdir -p "$DIR"
	} fi
	if [ ! -d $DIR ] ; then {
		echo "Oops: $DIR failed to create directory"
		exit -1
	} fi
} done

PY_DIR=$PWD

# Setup py scripts
cd $TMP_DIR
for SCRIPT in $SEARCH_SCRIPT $FILTER_SCRIPT ; do {
	if [ ! -h $SCRIPT ] ; then {
		ln -s $PY_DIR/$SCRIPT || exit -1
	} fi
} done

# search
python $SEARCH_SCRIPT -i $ITER -o $TMP_DIR -p $PRECISION -a 1 -b 7 -l [30:32] -f 1 -s $SYMMETRY || exit -1

# copy only the ones containing a solution
python $FILTER_SCRIPT $GIT_DIR $TMP_DIR

# do the git stuff
cd $GIT_DIR
if [ ! -d .git ]; then {
	GIT_INIT="YES"
	git init
} fi

# commit modified:
MOD_FILES=$(git status | grep modified | awk '{print $3}')
for FILE in $MOD_FILES $NEW_FILES; do
	GREP_RES=$(git diff "$FILE" | grep -e '^\+    \[')
	if [ -n "$GREP_RES" ] ; then
		IS_DYN=$(echo "$DYN_FILES" | grep "$FILE")
		if [ -z $IS_DYN ] ; then
			git add "$FILE"
		fi
	fi
done

NEW_FILES=$(git status | grep -e '#	frh-roots.*.py' | awk '{print $2}')
for FILE in $MOD_FILES $NEW_FILES; do
	GREP_RES=$(grep -e '^    \[' "$FILE" )
	if [ -n "$GREP_RES" ] ; then
		IS_DYN=$(echo "$DYN_FILES" | grep "$FILE")
		if [ -z $IS_DYN ] ; then
			git add "$FILE"
		fi
	fi
done

# make a tmp commit with tmp message (if needed):
if [ -z $GIT_INIT ] ; then {
	NR_OF_NEW_SOLS=$(git diff --cached | grep -c '^\+    \[')
	NR_OF_RMED_SOLS=$(git diff --cached | grep -c '^\-    \[')
} else {
	NR_OF_NEW_SOLS=$(cat frh-roots*.py | grep -c '^    \[')
	NR_OF_RMED_SOLS='0'
} fi
MSG=$(date +%Y-%m-%d)
MSG="$MSG: Add $NR_OF_NEW_SOLS solution"
# MSG grammar: use plural if more than 1 solution
if (($NR_OF_NEW_SOLS > 1)) ; then
	MSG="$MSG"s
fi
# Add removals to MSG
if (($NR_OF_RMED_SOLS > 0)) ; then
	MSG="$MSG (delete $NR_OF_RMED_SOLS)"
fi
# only commit if needed
if [[ (($NR_OF_NEW_SOLS > 0)) || (($NR_OF_RMED_SOLS > 0)) ]] ; then
	git commit -m "$MSG"
	echo "commited \"$MSG\""
	if (($NR_OF_RMED_SOLS > 0)) ; then
		echo "**** Warning: the commit removes $NR_OF_RMED_SOLS existing solution(s)"
	fi
else
	echo "Nothing to be commited"
fi

# ignore all files that are just an increase of the nr of iterations:
# or dynamic files
git reset --hard
