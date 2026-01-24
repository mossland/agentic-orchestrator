import { ethers } from "hardhat";

async function main() {
  const Contract = await ethers.getContractFactory("Contract");
  const contract = await Contract.deploy("MyContract");
  await contract.waitForDeployment();

  console.log("Contract deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
