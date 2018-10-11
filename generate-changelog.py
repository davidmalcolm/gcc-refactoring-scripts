import unittest
    def write(self, msg):
        sys.stdout.write(msg)

                self.write('\n')
                self.write('%s\n' % line.strip())
                self.write('%s/ChangeLog:\n' % dir_)
            self.write('\t* %s' % rel_path)
                self.write(': %s\n' % text)
                self.write(' ')
                self.write(startline)
                self.write('%s(%s): Likewise.\n' % (indent, scope))
            self.write('%s%s\n' % (' ' * 16, line.rstrip()))
class TestParser(Parser):
    def __init__(self, omit_hunks, show_linenums):
        Parser.__init__(self, omit_hunks, show_linenums)
        self.text = ''

    def write(self, msg):
        self.text += msg

class TestGenerateChangeLog(unittest.TestCase):
    def get_clog(self, diff):
        p = TestParser(False, False)
        p.cll.dirs = ['./libcpp', './gcc/testsuite']
        for line in diff.splitlines():
            # TODO: after py3k we can use keepends=True
            line += '\n'
            p.on_line(line)
        return p.text

    def test_simple(self):
        diff = """
diff --git a/libcpp/macro.c b/libcpp/macro.c
index 073816d..aacaf8c 100644
--- a/libcpp/macro.c
+++ b/libcpp/macro.c
@@ -964,6 +964,10 @@ _cpp_arguments_ok (cpp_reader *pfile, cpp_macro *macro, const cpp_hashnode *node
               "macro \"%s\" passed %u arguments, but takes just %u",
               NODE_NAME (node), argc, macro->paramc);
 
+  if (macro->line > RESERVED_LOCATION_COUNT)
+    cpp_error_at (pfile, CPP_DL_NOTE, macro->line, "macro \"%s\" defined here",
+                 NODE_NAME (node));
+
   return false;
 }
"""
        clog = self.get_clog(diff)
        self.assertMultiLineEqual(clog,
                                  """
libcpp/ChangeLog:
	* macro.c (_cpp_arguments_ok): Likewise.
                               "macro "%s" passed %u arguments, but takes just %u",
                               NODE_NAME (node), argc, macro->paramc);
                
                +  if (macro->line > RESERVED_LOCATION_COUNT)
                +    cpp_error_at (pfile, CPP_DL_NOTE, macro->line, "macro "%s" defined here",
                +                 NODE_NAME (node));
                +
                   return false;
                 }
""")

    def test_added_file(self):
        diff = """
diff --git a/gcc/testsuite/c-c++-common/cpp/macro-arg-count-1.c b/gcc/testsuite/c-c++-common/cpp/macro-arg-count-1.c
new file mode 100644
index 0000000..7773c47
--- /dev/null
+++ b/gcc/testsuite/c-c++-common/cpp/macro-arg-count-1.c
@@ -0,0 +1,3 @@
+/* { dg-options "-fdiagnostics-show-caret" } */
+
+#define MACRO_1(X,Y) /* { dg-line "def_of_MACRO_1" } */
"""
        clog = self.get_clog(diff)
        self.assertMultiLineEqual(clog,
                                  """
gcc/testsuite/ChangeLog:
	* c-c++-common/cpp/macro-arg-count-1.c: New test.
                @@ -0,0 +1,3 @@
                +/* { dg-options "-fdiagnostics-show-caret" } */
                +
                +#define MACRO_1(X,Y) /* { dg-line "def_of_MACRO_1" } */
""")
    argp.add_argument('--test', help='run test suite',
                      action='store_true', default=False, dest='test')
    argp.add_argument('files', nargs='*')
    sys.argv = [sys.argv[0]] + parsed_args.files

    if parsed_args.test:
        unittest.main()