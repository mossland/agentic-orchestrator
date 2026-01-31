import { ethers } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with:", deployer.address);

  // Deploy main contract
  const Contract = await ethers.getContractFactory("Main");
  const contract = await Contract.deploy();
  await contract.waitForDeployment();

  console.log("Contract deployed to:", await contract.getAddress());

  // Verify contract on Etherscan (optional)
  // await run("verify:verify", {
  //   address: await contract.getAddress(),
  //   constructorArguments: [],
  // });
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
