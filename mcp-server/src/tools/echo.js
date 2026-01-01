// Simple example tool: echo
// Input: any JSON
// Output: { echoed: <input> }

exports.handle = async function(input) {
  return {
    echoed: input,
    message: 'echo tool received input'
  };
};
