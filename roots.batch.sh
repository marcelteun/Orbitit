#!/bin/bash -x
GIT_DIR=$PWD/batch_search/frh-A4
TMP_DIR=$PWD/batch_search/frh-A4/tmp
PY_DIR=$PWD
#ITER=10000
ITER=20
PRECISION=13
SYMMETRY=A4
SEARCH_SCRIPT=roots.batch.py
FILTER_SCRIPT=filter.py
SOLS_COUNT_FILE=sols_count.csv

check_and_create_dirs() {
	for DIR in $GIT_DIR $TMP_DIR ; do {
		if [ ! -d "$DIR" ] ; then {
			mkdir -p "$DIR"
		} fi
		if [ ! -d $DIR ] ; then {
			echo "Oops: $DIR failed to create directory"
			exit -1
		} fi
	} done
}

setup_py_script_links() {
	for SCRIPT in $SEARCH_SCRIPT $FILTER_SCRIPT ; do {
		if [ ! -h $SCRIPT ] ; then {
			ln -s $PY_DIR/$SCRIPT || exit -1
		} fi
	} done
}

searc_for_solutions() {
	python $SEARCH_SCRIPT -i $ITER -o $TMP_DIR -p $PRECISION -a 4 -b 0 -l 6 -f 0 -s $SYMMETRY || exit -1
	#python $SEARCH_SCRIPT -i $ITER -o $TMP_DIR -p $PRECISION -a 7 -s $SYMMETRY || exit -1
	#python $SEARCH_SCRIPT -i $ITER -o $TMP_DIR -p $PRECISION -s $SYMMETRY || exit -1
}

copy_to_git_dir_if_sols_found() {
	python $FILTER_SCRIPT $GIT_DIR $TMP_DIR
}

git_init_if_none() {
	if [ ! -d .git ]; then {
		GIT_INIT="YES"
		git init
	} fi
}

git_add_modified_with_new_sols() {
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
}

git_add_new_files() {
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
}

git_count_added_removed_sols() {
	if [ -z $GIT_INIT ] ; then {
		NR_OF_NEW_SOLS=$(git diff --cached | grep -c '^\+    \[')
		NR_OF_RMED_SOLS=$(git diff --cached | grep -c '^\-    \[')
	} else {
		NR_OF_NEW_SOLS=$(cat frh-roots*.py | grep -c '^    \[')
		NR_OF_RMED_SOLS='0'
	} fi
}

git_create_commit_message() {
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
}

git_commit_if_needed() {
	NETTO_NR_OF_SOLS=$(($NR_OF_NEW_SOLS - $NR_OF_RMED_SOLS))
	if [ -z $GIT_INIT ] ; then {
		echo "$ITER:$NETTO_NR_OF_SOLS" >> $SOLS_COUNT_FILE
	} else {
		echo "$ITER:$NETTO_NR_OF_SOLS" > $SOLS_COUNT_FILE
	} fi
	git add $SOLS_COUNT_FILE
	if [[ (($NR_OF_NEW_SOLS > 0)) || (($NR_OF_RMED_SOLS > 0)) ]] ; then
		git commit -m "$MSG"
		echo "commited \"$MSG\""
		if (($NR_OF_RMED_SOLS > 0)) ; then
			echo "**** Warning: the commit removes $NR_OF_RMED_SOLS existing solution(s)"
		fi
		unset GIT_INIT
	else
		git commit --amend -C HEAD
		echo "Nothing to commit"
	fi
}

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

check_and_create_dirs
cd $TMP_DIR
setup_py_script_links

while true; do {
	# search
	searc_for_solutions

	# copy only the ones containing a solution
	copy_to_git_dir_if_sols_found

	# do the git stuff
	cd $GIT_DIR
	git_init_if_none
	git_add_modified_with_new_sols
	git_add_new_files
	git_count_added_removed_sols
	git_create_commit_message
	git_commit_if_needed
	# ignore all files that are just an increase of the nr of iterations:
	# or dynamic files
	git reset --hard
	cd $TMP_DIR
} done
