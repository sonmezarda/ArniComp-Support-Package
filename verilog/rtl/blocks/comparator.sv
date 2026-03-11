module comparator(
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic less_flag,
    output logic equal_flag,
    output logic greater_flag
);

always_comb begin
    less_flag    = a < b;
    equal_flag   = a == b;
    greater_flag = a > b;
end

endmodule