import argparse
        self.new_file = False
            self.new_file = False
        if line.startswith('new file mode'):
            return

        if line == '--- /dev/null\n':
            self.new_file = True
            return

            sys.stdout.write('\t* %s' % rel_path)
            if self.new_file:
                text = 'New file.'
                if 'testsuite' in cll_path:
                    text = 'New test.'
                sys.stdout.write(': %s\n' % text)
            else:
                sys.stdout.write(' ')
                self.initial_hunk = True
                self.previous_scope = None
        if line.startswith('@') and not self.new_file: