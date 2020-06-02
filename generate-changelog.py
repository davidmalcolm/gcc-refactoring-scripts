NEW_FILE, DELETED_FILE, CHANGED_FILE = range(3)

        self.state = CHANGED_FILE
        self.filename = None
    def set_file(self, filename):
        if filename == self.filename:
            return
        self.filename = filename

        # Start of per-file changes
        git_path = filename # e.g. "gcc/gimple.h"
        cll_path = './%s' % git_path # e.g. "./gcc/gimple.h"
        dir_ = self.cll.locate_dir(cll_path) # e.g "./gcc"

        # Strip off leading "./":
        assert dir_.startswith('./')
        dir_ = dir_[2:]

        # Emit e.g. "gcc/ChangeLog:" whenever the enclosing ChangeLog
        # changes.
        if dir_ != self.current_dir:
            self.current_dir = dir_
            self.write('%s/ChangeLog:\n' % dir_)

        # Get path relative to the ChangeLog file
        # e.g. "gimple.h"
        rel_path = self.cll.get_path_relative_to_changelog(cll_path)
        self.write('\t* %s' % rel_path)
        if self.state in (NEW_FILE, DELETED_FILE):
            if self.state == NEW_FILE:
                text = 'New file.'
                if 'testsuite' in cll_path:
                    text = 'New test.'
            else:
                text = 'Deleted file.'
                if 'testsuite' in cll_path:
                    text = 'Deleted test.'
            self.write(': %s\n' % text)
        else:
            self.write(' ')
            self.initial_hunk = True
            self.previous_scope = None

            self.state = CHANGED_FILE
            self.filename = None
            self.state = NEW_FILE
            return
        if line.startswith('deleted file mode'):
            self.state = DELETED_FILE
        # e.g. '--- a/gcc/asan.c\n'
        m = re.match(r'--- a/(.+)', line)
        if m:
            self.set_file(m.group(1))
            return
        # e.g. '+++ b/gcc/asan.c\n'
            self.set_file(m.group(1))
            return
        if line == '+++ /dev/null\n':
        if line.startswith('@') and self.state == CHANGED_FILE:
            elif scope[0] == 'proc':
                # e.g. "struct foo"
                scope = scope[1]