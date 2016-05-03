#!/bin/bash

./munich_films.py --input=artechok_originalton.html -o test_out.txt

echo -n "*** Diff comparison with reference output... "
if (diff --brief test_out.txt reference_output.txt)
then
  echo " OK"
else
  echo "Diff output:"
  diff test_out.txt reference_output.txt
fi

